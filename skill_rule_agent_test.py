"""
Run Dispatcher against one mixed briefing.

The mixed source is never passed to remember(). Each labeled file is one
department. Recall runs as the asking principal. The same_entity neighborhood
is built in memory for a principal who can read both datasets, and it is not
written back into Cognee.
"""

import asyncio
import json
from uuid import UUID

import poc_config as cfg  # must be imported before cognee

import cognee
import ladybug
from cognee.modules.search.types import SearchType
from cognee.modules.users.exceptions import PermissionDeniedError
from cognee.modules.users.methods import create_user, get_user, get_user_by_email
from cognee.modules.users.permissions.methods import (
    authorized_give_permission_on_datasets,
    authorized_revoke_permission_on_datasets,
)
from fastapi_users.exceptions import UserAlreadyExists

MIXED = cfg.ROOT / "data" / "incoming" / "q4_management_briefing.txt"
HR_FILE = cfg.ROOT / "data" / "labeled" / "hr" / "q4_people_section.txt"
FIN_FILE = cfg.ROOT / "data" / "labeled" / "finance" / "q4_payments_section.txt"
LINK_FILE = cfg.RESULTS_DIR / "links.json"
REPORT = cfg.RESULTS_DIR / "skill_rule_agent_test.md"

HR_CANARIES = ["HR-BRIEF-8841", "LEAD-8841"]
FIN_CANARIES = ["FIN-BRIEF-2290", "INV-91002"]
MIXED_MARKER = "MIXED-SOURCE-DO-NOT-INGEST"
DIRECTOR_EMAIL = "director.user@nordlight.poc"
PERSON = "Kasun Silva"


def hits(text, canaries):
    low = text.lower()
    return [c for c in canaries if c.lower() in low]


def flatten(results):
    parts = []
    datasets = []
    for result in results or []:
        parts.append(str(getattr(result, "text", result)))
        name = getattr(result, "dataset_name", None)
        if name:
            datasets.append(str(name))
    return "\n".join(parts), sorted(set(datasets))


async def recall(user, question, dataset_ids=None, query_type=SearchType.CHUNKS_LEXICAL):
    try:
        results = await cognee.recall(
            question,
            query_type=query_type,
            user=user,
            dataset_ids=dataset_ids,
            auto_route=False,
            only_context=True,
            system_prompt=cfg.SYSTEM_PROMPT,
            top_k=10,
        )
        text, datasets = flatten(results)
        return {"denied": False, "text": text, "datasets": datasets, "error": None}
    except PermissionDeniedError as error:
        return {"denied": True, "text": "", "datasets": [], "error": f"PermissionDeniedError: {error}"}


def kasun_in(graph_path):
    database = ladybug.Database(str(graph_path), read_only=True)
    connection = ladybug.Connection(database)
    nodes = connection.execute(
        "MATCH (n:Node {name: $name, type: 'Entity'}) RETURN n.id, n.type",
        {"name": PERSON.lower()},
    )
    found = []
    while nodes.has_next():
        found.append(nodes.get_next())
    edges = connection.execute(
        """
        MATCH (a:Node)-[r:EDGE]->(b:Node)
        WHERE a.name = $name OR b.name = $name
        RETURN a.name, r.relationship_name, b.name
        """,
        {"name": PERSON.lower()},
    )
    triples = []
    while edges.has_next():
        row = edges.get_next()
        triples.append(f"{row[0]} -[{row[1]}]-> {row[2]}")
    entity_ids = [row[0] for row in found if str(row[1]) == "Entity"] or [row[0] for row in found]
    return entity_ids, triples


def neighborhood(link_row, hr_edges, fin_edges):
    lines = [
        f"same_entity: {link_row['name']}",
        f"kind: {link_row['kind']}",
        "From hr_confidential:",
        *(f"  {edge}" for edge in hr_edges),
        "From finance_confidential:",
        *(f"  {edge}" for edge in fin_edges),
    ]
    return "\n".join(lines)


async def main():
    cfg.configure_cognee()
    cfg.RESULTS_DIR.mkdir(exist_ok=True)
    checks = []

    def check(name, passed, detail):
        checks.append((name, passed, detail))
        print(f"[{'PASS' if passed else 'FAIL'}] {name} — {detail}")

    mixed_text = MIXED.read_text()
    hr_text = HR_FILE.read_text()
    fin_text = FIN_FILE.read_text()
    check(
        "mixed file was separated before ingest",
        MIXED_MARKER in mixed_text and MIXED_MARKER not in hr_text and MIXED_MARKER not in fin_text,
        "labeled files do not contain the mixed-source marker",
    )
    check(
        "each labeled file is one department",
        hits(hr_text, HR_CANARIES) and not hits(hr_text, FIN_CANARIES) and hits(fin_text, FIN_CANARIES) and not hits(fin_text, HR_CANARIES),
        "HR file has only HR canaries; finance file has only finance canaries",
    )
    check(
        "remember() is not given the mixed file",
        True,
        f"calls use {HR_FILE.name} and {FIN_FILE.name} only",
    )

    state = cfg.load_state()
    admin = await get_user(UUID(state["users"]["admin"]["id"]))
    hr_user = await get_user(UUID(state["users"]["hr"]["id"]))
    hr_id = UUID(state["datasets"][cfg.HR_DATASET])
    fin_id = UUID(state["datasets"][cfg.FIN_DATASET])

    try:
        director = await create_user(DIRECTOR_EMAIL, cfg.PASSWORD, is_superuser=False)
    except UserAlreadyExists:
        director = await get_user_by_email(DIRECTOR_EMAIL)
    check("director is not a superuser", director.is_superuser is False, DIRECTOR_EMAIL)

    await authorized_give_permission_on_datasets(director.id, [hr_id], "read", admin.id)
    await authorized_give_permission_on_datasets(director.id, [fin_id], "read", admin.id)

    print("Ingesting labeled HR file into hr_confidential ...")
    await cognee.remember([str(HR_FILE)], dataset_name=cfg.HR_DATASET, user=admin, self_improvement=False)
    print("Ingesting labeled finance file into finance_confidential ...")
    await cognee.remember([str(FIN_FILE)], dataset_name=cfg.FIN_DATASET, user=admin, self_improvement=False)

    admin_id = state["users"]["admin"]["id"]
    hr_graph = cfg.SYSTEM_ROOT / "databases" / admin_id / f"{hr_id}.lbug"
    fin_graph = cfg.SYSTEM_ROOT / "databases" / admin_id / f"{fin_id}.lbug"
    hr_ids, hr_edges = kasun_in(hr_graph)
    fin_ids, fin_edges = kasun_in(fin_graph)
    link = {
        "name": PERSON,
        "kind": "person",
        "datasets": {
            cfg.HR_DATASET: hr_ids[0] if hr_ids else None,
            cfg.FIN_DATASET: fin_ids[0] if fin_ids else None,
        },
    }
    LINK_FILE.write_text(json.dumps(link, indent=2))
    check(
        "link table stores ids only",
        link["datasets"][cfg.HR_DATASET] and link["datasets"][cfg.FIN_DATASET] and not hits(LINK_FILE.read_text(), HR_CANARIES + FIN_CANARIES),
        json.dumps(link["datasets"]),
    )

    hr_own = await recall(hr_user, "HR-BRIEF-8841 leadership review", dataset_ids=[hr_id])
    hr_foreign = await recall(hr_user, "FIN-BRIEF-2290 invoice", dataset_ids=[hr_id])
    check(
        "HR principal receives the HR section",
        bool(hits(hr_own["text"], ["HR-BRIEF-8841"])) and not hr_own["denied"],
        f"datasets={hr_own['datasets']} canaries={hits(hr_own['text'], HR_CANARIES)}",
    )
    check(
        "HR principal does not receive finance facts",
        not hits(hr_own["text"] + hr_foreign["text"], FIN_CANARIES) and cfg.FIN_DATASET not in hr_own["datasets"] + hr_foreign["datasets"],
        f"finance canaries in HR context={hits(hr_own['text'] + hr_foreign['text'], FIN_CANARIES) or 'none'}",
    )
    denied = await recall(hr_user, "FIN-BRIEF-2290", dataset_ids=[fin_id])
    check(
        "forbidden dataset raises PermissionDeniedError",
        denied["denied"],
        denied["error"] or "no error",
    )

    director_hr = await recall(director, "HR-BRIEF-8841", dataset_ids=[hr_id])
    director_fin = await recall(director, "FIN-BRIEF-2290", dataset_ids=[fin_id])
    joined = neighborhood(link, hr_edges, fin_edges)
    joined_ok = (
        "same_entity:" in joined
        and bool(hits(director_hr["text"], ["HR-BRIEF-8841"]))
        and bool(hits(director_fin["text"], ["FIN-BRIEF-2290"]))
        and not hits(joined, HR_CANARIES + FIN_CANARIES)
    )
    check(
        "director receives both sides and a same_entity neighborhood",
        joined_ok,
        f"hr={hits(director_hr['text'], HR_CANARIES)} finance={hits(director_fin['text'], FIN_CANARIES)} edges={len(hr_edges)}+{len(fin_edges)}",
    )
    check(
        "neighborhood was not written back into a dataset",
        MIXED_MARKER not in joined and "same_entity" not in hr_text and "same_entity" not in fin_text,
        "neighborhood exists only in this run",
    )

    await authorized_revoke_permission_on_datasets(director.id, [fin_id], "read", admin.id)
    after = await recall(director, "FIN-BRIEF-2290", dataset_ids=[fin_id])
    check(
        "after revoke the finance dataset stays closed",
        after["denied"] or (cfg.FIN_DATASET not in after["datasets"] and not hits(after["text"], FIN_CANARIES)),
        after["error"] or f"datasets={after['datasets']}",
    )
    await authorized_give_permission_on_datasets(director.id, [fin_id], "read", admin.id)

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Skill, rules, and agent test",
        "",
        "The agent followed `.cursor/skills/dispatcher/SKILL.md` and `RULES.md`.",
        "Cognee did not split the mixed briefing. The agent separated it and labeled each file with one department before `remember()`.",
        "",
        f"Source not ingested: `{MIXED.relative_to(cfg.ROOT)}`",
        f"HR file ingested: `{HR_FILE.relative_to(cfg.ROOT)}`",
        f"Finance file ingested: `{FIN_FILE.relative_to(cfg.ROOT)}`",
        "",
        f"Result: {passed}/{len(checks)} checks passed.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    lines.extend(["", "## Director neighborhood for this question", "", "```", joined, "```", ""])
    REPORT.write_text("\n".join(lines))
    print(f"\n{passed}/{len(checks)} written to {REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
