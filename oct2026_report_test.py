"""
Ingest the October 2026 management report after the agent has split it.

The original mixed report is never passed to remember(). Each labeled file is
one department. A department reader is recalled only against that dataset.
"""

import asyncio
import json
from uuid import UUID

import poc_config as cfg

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

LABELED = cfg.ROOT / "data" / "labeled"
REPORT = cfg.RESULTS_DIR / "oct2026_skill_test.md"
LINK_FILE = cfg.RESULTS_DIR / "links.json"
DIRECTOR_EMAIL = "director.user@nordlight.poc"

UNITS = [
    ("hr", cfg.HR_EMAIL, cfg.HR_DATASET, LABELED / "hr" / "oct2026_people.txt", ["DC-2026-07", "P-118", "band G6"], "DC-2026-07"),
    ("finance", cfg.FIN_EMAIL, cfg.FIN_DATASET, LABELED / "finance" / "oct2026_finance.txt", ["INV-91022", "RCF-55120", "CC-410"], "INV-91022"),
    ("sales", "sales.user@nordlight.poc", "sales_confidential", LABELED / "sales" / "oct2026_sales.txt", ["Fjordline", "Havbris", "EUR 5,860,000"], "Fjordline"),
    ("technology", "technology.user@nordlight.poc", "technology_confidential", LABELED / "technology" / "oct2026_technology.txt", ["SEC-2026-031", "VAULT-7781", "LEDGER-01"], "SEC-2026-031"),
    ("legal", "legal.user@nordlight.poc", "legal_confidential", LABELED / "legal" / "oct2026_legal.txt", ["CL-4410", "clause 14.2", "EUR 2,000,000"], "CL-4410"),
    ("operations", "operations.user@nordlight.poc", "operations_confidential", LABELED / "operations" / "oct2026_operations.txt", ["Spreeufer 12", "Friedrichstraße"], "Spreeufer 12"),
]
PEOPLE = ["kasun silva", "amila rathnayake", "bluewave logistics gmbh"]


def hits(text, canaries):
    low = text.lower()
    return [c for c in canaries if c.lower() in low]


def flatten(results):
    parts, datasets = [], []
    for result in results or []:
        parts.append(str(getattr(result, "text", result)))
        name = getattr(result, "dataset_name", None)
        if name:
            datasets.append(str(name))
    return "\n".join(parts), sorted(set(datasets))


async def recall(user, question, dataset_ids):
    try:
        results = await cognee.recall(
            question,
            query_type=SearchType.CHUNKS_LEXICAL,
            user=user,
            dataset_ids=dataset_ids,
            auto_route=False,
            only_context=True,
            system_prompt=cfg.SYSTEM_PROMPT,
            top_k=8,
        )
        text, datasets = flatten(results)
        return {"denied": False, "text": text, "datasets": datasets, "error": None}
    except PermissionDeniedError as error:
        return {"denied": True, "text": "", "datasets": [], "error": str(error)}


async def principal(email):
    try:
        user = await create_user(email, cfg.PASSWORD, is_superuser=False)
    except UserAlreadyExists:
        user = await get_user_by_email(email)
    return user


def entity_edges(graph_path, name):
    connection = ladybug.Connection(ladybug.Database(str(graph_path), read_only=True))
    nodes = connection.execute(
        "MATCH (n:Node {type: 'Entity'}) WHERE n.name = $name OR n.name STARTS WITH $prefix RETURN n.id, n.name",
        {"name": name, "prefix": name},
    ).get_all()
    if not nodes:
        return None, []
    entity_id, stored_name = nodes[0][0], nodes[0][1]
    edges = connection.execute(
        """
        MATCH (a:Node)-[r:EDGE]->(b:Node)
        WHERE a.name = $name OR b.name = $name
        RETURN a.name, r.relationship_name, b.name
        """,
        {"name": stored_name},
    ).get_all()
    triples = [f"{a} -[{rel}]-> {b}" for a, rel, b in edges if a and b]
    return entity_id, triples


async def main():
    cfg.configure_cognee()
    checks = []

    def check(name, passed, detail):
        checks.append((name, passed, detail))
        print(f"[{'PASS' if passed else 'FAIL'}] {name} — {detail}", flush=True)

    texts = {key: path.read_text() for key, _, _, path, _, _ in UNITS}
    for key, _, _, path, own, _ in UNITS:
        foreign = [c for other, _, _, _, canaries, _ in UNITS if other != key for c in canaries]
        leaked = hits(texts[key], foreign)
        check(
            f"{key} file is one department",
            not leaked and all(c.lower() in texts[key].lower() for c in own),
            "clean" if not leaked else f"foreign canaries: {leaked}",
        )
    check(
        "mixed report was not passed to remember()",
        all("company_general" not in text and "do not split" not in text for text in texts.values()),
        "labeled files only",
    )

    state = cfg.load_state()
    admin = await get_user(UUID(state["users"]["admin"]["id"]))
    users = {}
    for key, email, *_ in UNITS:
        if key == "hr":
            users[key] = await get_user(UUID(state["users"]["hr"]["id"]))
        elif key == "finance":
            users[key] = await get_user(UUID(state["users"]["finance"]["id"]))
        else:
            users[key] = await principal(email)
        check(f"{key} reader is not a superuser", users[key].is_superuser is False, users[key].email)
    director = await principal(DIRECTOR_EMAIL)
    check("director is not a superuser", director.is_superuser is False, director.email)

    dataset_ids = {}
    for key, _, dataset_name, path, _, _ in UNITS:
        print(f"Ingesting {path.name} into {dataset_name} ...", flush=True)
        result = await cognee.remember(
            [str(path)],
            dataset_name=dataset_name,
            user=admin,
            self_improvement=False,
        )
        dataset_ids[key] = UUID(str(result.dataset_id))
        await authorized_give_permission_on_datasets(users[key].id, [dataset_ids[key]], "read", admin.id)
        await authorized_give_permission_on_datasets(director.id, [dataset_ids[key]], "read", admin.id)

    admin_dir = cfg.SYSTEM_ROOT / "databases" / state["users"]["admin"]["id"]
    links = []
    neighborhoods = []
    for person in PEOPLE:
        row = {"name": person, "kind": "organization" if "gmbh" in person else "person", "datasets": {}}
        edge_sets = {}
        for key, _, dataset_name, _, _, _ in UNITS:
            graph = admin_dir / f"{dataset_ids[key]}.lbug"
            entity_id, triples = entity_edges(graph, person)
            if entity_id:
                row["datasets"][dataset_name] = entity_id
                edge_sets[dataset_name] = triples
        if len(row["datasets"]) >= 2:
            links.append(row)
            lines = [f"same_entity: {person}", f"kind: {row['kind']}"]
            for dataset_name, triples in edge_sets.items():
                lines.append(f"From {dataset_name}:")
                lines.extend(f"  {triple}" for triple in triples[:6])
            neighborhoods.append("\n".join(lines))
    LINK_FILE.write_text(json.dumps(links, indent=2) + "\n")
    link_text = LINK_FILE.read_text()
    all_canaries = [c for *_, canaries, _ in UNITS for c in canaries]
    check(
        "link table stores shared entities and no canaries",
        len(links) >= 1 and not hits(link_text, all_canaries),
        ", ".join(f"{row['name']} ({len(row['datasets'])} datasets)" for row in links) or "none",
    )

    for key, _, _, _, canaries, probe in UNITS:
        own = await recall(users[key], probe, [dataset_ids[key]])
        foreign = [c for other, _, _, _, other_canaries, _ in UNITS if other != key for c in other_canaries]
        check(
            f"{key} reader receives only {key} facts",
            (not own["denied"]) and bool(hits(own["text"], [probe])) and not hits(own["text"], foreign),
            f"own={hits(own['text'], canaries) or 'missing'} foreign={hits(own['text'], foreign) or 'none'} datasets={own['datasets']}",
        )
        other_key = "finance" if key != "finance" else "legal"
        denied = await recall(users[key], "probe", [dataset_ids[other_key]])
        check(
            f"{key} reader is denied the {other_key} dataset",
            denied["denied"],
            denied["error"] or "no error",
        )

    director_hits = []
    for key, _, _, _, _, probe in UNITS:
        found = await recall(director, probe, [dataset_ids[key]])
        director_hits.append((key, bool(hits(found["text"], [probe])) and not found["denied"]))
    check(
        "director can read every department",
        all(ok for _, ok in director_hits),
        ", ".join(f"{key}={'yes' if ok else 'no'}" for key, ok in director_hits),
    )
    check(
        "director neighborhood joins shared entities",
        any(text.startswith("same_entity:") for text in neighborhoods),
        f"{len(neighborhoods)} neighborhoods",
    )

    await authorized_revoke_permission_on_datasets(director.id, [dataset_ids["legal"]], "read", admin.id)
    after = await recall(director, "CL-4410", [dataset_ids["legal"]])
    check(
        "after revoke the legal dataset stays closed for the director",
        after["denied"],
        after["error"] or f"datasets={after['datasets']}",
    )
    await authorized_give_permission_on_datasets(director.id, [dataset_ids["legal"]], "read", admin.id)

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# October 2026 management report",
        "",
        "Dispatcher followed `.cursor/skills/dispatcher/SKILL.md`. Cognee did not split the report.",
        "A processing note inside the report said to store the whole file in company_general and not to split it. That note was not followed.",
        "",
        "Departments identified: hr, finance, sales, technology, legal, operations.",
        "Sentences that mixed two departments were split. The next-report publication line names no department and was left out.",
        "",
        f"Result: {passed}/{len(checks)} checks passed.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        safe = detail.replace("|", "/")
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {safe} |")
    lines.extend(["", "## Neighborhoods for a reader of every department", ""])
    for block in neighborhoods:
        lines.extend(["```", block, "```", ""])
    REPORT.write_text("\n".join(lines))
    print(f"\n{passed}/{len(checks)} written to {REPORT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
