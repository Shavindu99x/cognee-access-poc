"""
Ingest the Brightmoor Q3 2026 management report after Dispatcher has split it.

The original mixed report is never passed to remember(). Each labeled file is
one audience. A department reader is recalled only against that dataset.
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

LABELED = cfg.ROOT / "data" / "labeled" / "brightmoor"
REPORT = cfg.RESULTS_DIR / "brightmoor_skill_test.md"
LINK_FILE = cfg.RESULTS_DIR / "brightmoor_links.json"
DIRECTOR_EMAIL = "director.user@brightmoor.poc"

UNITS = [
    ("general", "general.user@brightmoor.poc", "brightmoor_general", LABELED / "general.txt", ["travel policy", "summer party"], "summer party"),
    ("product", "product.user@brightmoor.poc", "brightmoor_product", LABELED / "product.txt", ["PM-0912", "KESTREL"], "PM-0912"),
    ("finance", "finance.user@brightmoor.poc", "brightmoor_finance", LABELED / "finance.txt", ["INV-24417", "EUR 21,650,000", "EUR 165 million", "EUR 9,800,000"], "INV-24417"),
    ("sales", "sales.user@brightmoor.poc", "brightmoor_sales", LABELED / "sales.txt", ["Brandvik", "EUR 4,960,000"], "Brandvik"),
    ("people", "people.user@brightmoor.poc", "brightmoor_people", LABELED / "people.txt", ["CS-3381", "Imesha Fonseka", "EUR 185,000", "band E5"], "CS-3381"),
    ("it_security", "security.user@brightmoor.poc", "brightmoor_it_security", LABELED / "it_security.txt", ["SEC-INC-0814", "PT-26-01"], "SEC-INC-0814"),
    ("legal", "legal.user@brightmoor.poc", "brightmoor_legal", LABELED / "legal.txt", ["LGL-2231", "LGL-2207", "EP-26-118"], "LGL-2231"),
    ("strategy", "strategy.user@brightmoor.poc", "brightmoor_strategy", LABELED / "strategy.txt", ["Quillstream", "EUR 22 to 26 million"], "Quillstream"),
]

# Real-world entities that the source names in more than one audience.
SHARED = [
    ("tessaro", "organization"),
    ("medrava", "organization"),
    ("kirkwall", "organization"),
    ("corvane", "organization"),
    ("mareike lorenz", "person"),
    ("lukas hoffmann", "person"),
]


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


def matching_entity(graph_path, needle):
    connection = ladybug.Connection(ladybug.Database(str(graph_path), read_only=True))
    nodes = connection.execute(
        "MATCH (n:Node {type: 'Entity'}) WHERE n.name CONTAINS $needle RETURN n.id, n.name",
        {"needle": needle},
    ).get_all()
    if not nodes:
        return None, None, []
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
    return entity_id, stored_name, triples


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
            f"{key} file is one audience",
            not leaked and all(c.lower() in texts[key].lower() for c in own),
            "clean" if not leaked else f"foreign canaries: {leaked}",
        )

    state = cfg.load_state()
    admin = await get_user(UUID(state["users"]["admin"]["id"]))
    check("admin is not a superuser", admin.is_superuser is False, admin.email)

    users = {}
    for key, email, *_ in UNITS:
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
    for needle, kind in SHARED:
        row = {"name": needle, "kind": kind, "datasets": {}}
        edge_sets = {}
        for key, _, dataset_name, _, _, _ in UNITS:
            graph = admin_dir / f"{dataset_ids[key]}.lbug"
            entity_id, stored_name, triples = matching_entity(graph, needle)
            if entity_id:
                row["datasets"][dataset_name] = entity_id
                edge_sets[dataset_name] = triples
                row["stored_as"] = stored_name
        if len(row["datasets"]) >= 2:
            links.append(row)
            lines = [f"same_entity: {needle}", f"kind: {kind}"]
            for dataset_name, triples in edge_sets.items():
                lines.append(f"From {dataset_name}:")
                lines.extend(f"  {triple}" for triple in triples[:6])
            neighborhoods.append("\n".join(lines))
    LINK_FILE.write_text(json.dumps(links, indent=2) + "\n")
    link_text = LINK_FILE.read_text()
    all_canaries = [c for *_, canaries, _ in UNITS for c in canaries]
    check(
        "link table stores shared entities and no canaries",
        len(links) >= 2 and not hits(link_text, all_canaries),
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
        other_key = "legal" if key != "legal" else "finance"
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
        "director can read every Brightmoor audience",
        all(ok for _, ok in director_hits),
        ", ".join(f"{key}={'yes' if ok else 'no'}" for key, ok in director_hits),
    )
    check(
        "director neighborhood joins shared entities",
        len(neighborhoods) >= 2,
        f"{len(neighborhoods)} neighborhoods",
    )

    people_only = await recall(users["people"], "Quillstream", [dataset_ids["strategy"]])
    check(
        "people reader is denied the strategy dataset",
        people_only["denied"],
        people_only["error"] or "no error",
    )

    await authorized_revoke_permission_on_datasets(director.id, [dataset_ids["legal"]], "read", admin.id)
    after = await recall(director, "LGL-2231", [dataset_ids["legal"]])
    check(
        "after revoke the legal dataset stays closed for the director",
        after["denied"],
        after["error"] or f"datasets={after['datasets']}",
    )
    still = await recall(director, "Quillstream", [dataset_ids["strategy"]])
    check(
        "after the legal revoke the director can still read strategy",
        (not still["denied"]) and bool(hits(still["text"], ["Quillstream"])),
        f"denied={still['denied']} datasets={still['datasets']}",
    )
    await authorized_give_permission_on_datasets(director.id, [dataset_ids["legal"]], "read", admin.id)

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Brightmoor Q3 2026 management report",
        "",
        "Dispatcher followed `.cursor/skills/dispatcher/SKILL.md` and `.cursor/skills/dispatcher/RULES.md`.",
        "Cognee did not split the report. The mixed source was never passed to `remember()`.",
        "The cover line Classification: Confidential was not treated as permission to store the whole file in one dataset.",
        "",
        "Audiences: company_general, product, finance, sales, people, it_security, legal, strategy.",
        "These are Brightmoor datasets. They were not added to the Nordlight datasets.",
        "A heading did not decide the audience. Hosting cost went to finance. The resignation, the grievance, pay, and parental leave went to people. The AGPL advice and the service-credit claim went to legal. Quillstream stayed in strategy.",
        "",
        f"Result: {passed}/{len(checks)} checks passed.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        safe = detail.replace("|", "/")
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {safe} |")
    lines.extend(["", "## Neighborhoods for a reader of every Brightmoor audience", ""])
    for block in neighborhoods:
        lines.extend(["```", block, "```", ""])
    lines.extend([
        "",
        "The neighborhood is built for this question only. It is not written back with `remember()`.",
        "",
    ])
    REPORT.write_text("\n".join(lines))
    print(f"\n{passed}/{len(checks)} written to {REPORT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
