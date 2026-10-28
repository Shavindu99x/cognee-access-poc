"""
Ingest the structured Brightmoor Q3 report after Dispatcher has labeled each section.

Each section already names one audience, so the section is stored whole.
The mixed source is never passed to remember().
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

LABELED = cfg.ROOT / "data" / "labeled" / "brightmoor_structured"
REPORT = cfg.RESULTS_DIR / "structured_skill_test.md"
LINK_FILE = cfg.RESULTS_DIR / "structured_links.json"

UNITS = [
    ("company", "company_general", LABELED / "company_general.txt", ["passed 400 customers", "summer party", "travel policy", "officially opened"], "summer party"),
    ("board", "board_confidential", LABELED / "board_confidential.txt", ["Quillstream", "165 million", "14 roles", "step down as CEO", "succession committee", "Corvane"], "Quillstream"),
    ("finance", "finance_confidential", LABELED / "finance_confidential.txt", ["1,870,000", "21,650,000", "INV-24417", "412,300", "9,800,000", "EUR 150,000"], "INV-24417"),
    ("people", "people_confidential", LABELED / "people_confidential.txt", ["Tobias Krämer", "CS-3381", "EUR 185,000", "Imesha Fonseka", "4.5 percent", "parental leave", "EUR 78,000"], "CS-3381"),
    ("gtm", "gtm_confidential", LABELED / "gtm_confidential.txt", ["4,960,000", "EUR 610,000", "Brandvik", "830,000", "114%", "18 percent"], "Brandvik"),
    ("engineering", "engineering_internal", LABELED / "engineering_internal.txt", ["PM-0912", "KESTREL", "47 minutes", "spot instances", "workflow designer", "site reliability engineers"], "KESTREL"),
    ("security", "security_confidential", LABELED / "security_confidential.txt", ["SEC-INC-0814", "PT-26-01", "SOC 2", "37 accounts", "billing system", "Secret scanning"], "SEC-INC-0814"),
    ("legal", "legal_confidential", LABELED / "legal_confidential.txt", ["LGL-2231", "LGL-2207", "EP-26-118", "EUR 240,000", "standard contractual clauses"], "LGL-2231"),
]

READERS = {
    "employee": ("employee@brightmoor.poc", ["company"]),
    "finance": ("finance.team@brightmoor.poc", ["company", "finance"]),
    "people": ("people.team@brightmoor.poc", ["company", "people"]),
    "gtm": ("gtm.lead@brightmoor.poc", ["company", "gtm"]),
    "engineering": ("engineering.user@brightmoor.poc", ["company", "engineering"]),
    "security": ("security.team@brightmoor.poc", ["company", "security"]),
    "legal": ("legal.team@brightmoor.poc", ["company", "legal"]),
    "cto": ("cto.user@brightmoor.poc", ["company", "engineering", "security"]),
    "board": ("board.user@brightmoor.poc", ["company", "board", "finance", "people", "gtm", "security", "legal"]),
    "director": ("director.user@brightmoor.poc", [key for key, *_ in UNITS]),
}

SHARED = [
    ("sofia brandt", "person"),
    ("lukas hoffmann", "person"),
    ("medrava", "organization"),
    ("kirkwall", "organization"),
    ("brightmoor flow", "product"),
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

    by_key = {key: (dataset_name, path, canaries, probe) for key, dataset_name, path, canaries, probe in UNITS}
    texts = {key: path.read_text() for key, _, path, _, _ in UNITS}
    for key, _, _, own, _ in UNITS:
        foreign = [c for other, _, _, canaries, _ in UNITS if other != key for c in canaries]
        leaked = hits(texts[key], foreign)
        check(
            f"{key} section is one audience",
            not leaked and all(c.lower() in texts[key].lower() for c in own),
            "clean" if not leaked else f"foreign canaries: {leaked}",
        )

    state = cfg.load_state()
    admin = await get_user(UUID(state["users"]["admin"]["id"]))
    check("admin is not a superuser", admin.is_superuser is False, admin.email)

    users = {}
    for name, (email, _) in READERS.items():
        users[name] = await principal(email)
        check(f"{name} reader is not a superuser", users[name].is_superuser is False, users[name].email)

    dataset_ids = {}
    for key, dataset_name, path, _, _ in UNITS:
        print(f"Ingesting {path.name} into {dataset_name} ...", flush=True)
        result = await cognee.remember(
            [str(path)],
            dataset_name=dataset_name,
            user=admin,
            self_improvement=False,
        )
        dataset_ids[key] = UUID(str(result.dataset_id))

    for name, (_, allowed) in READERS.items():
        allowed_ids = [dataset_ids[key] for key in allowed]
        await authorized_give_permission_on_datasets(users[name].id, allowed_ids, "read", admin.id)

    admin_dir = cfg.SYSTEM_ROOT / "databases" / state["users"]["admin"]["id"]
    links = []
    edge_sets_by_needle = {}
    for needle, kind in SHARED:
        row = {"name": needle, "kind": kind, "datasets": {}}
        edge_sets = {}
        for key, dataset_name, _, _, _ in UNITS:
            graph = admin_dir / f"{dataset_ids[key]}.lbug"
            entity_id, stored_name, triples = matching_entity(graph, needle)
            if entity_id:
                row["datasets"][dataset_name] = entity_id
                edge_sets[dataset_name] = triples
                row["stored_as"] = stored_name
        if len(row["datasets"]) >= 2:
            links.append(row)
            edge_sets_by_needle[needle] = edge_sets
    LINK_FILE.write_text(json.dumps(links, indent=2) + "\n")
    all_canaries = [c for *_, canaries, _ in UNITS for c in canaries]
    check(
        "link table stores shared entities and no canaries",
        len(links) >= 2 and not hits(LINK_FILE.read_text(), all_canaries),
        ", ".join(f"{row['name']} ({len(row['datasets'])} datasets)" for row in links) or "none",
    )

    def readable_names(allowed):
        return {by_key[key][0] for key in allowed}

    def neighborhood_for(allowed):
        readable = readable_names(allowed)
        blocks = []
        for row in links:
            if set(row["datasets"]) <= readable:
                lines = [f"same_entity: {row['name']}", f"kind: {row['kind']}"]
                for dataset_name, triples in edge_sets_by_needle[row["name"]].items():
                    lines.append(f"From {dataset_name}:")
                    lines.extend(f"  {triple}" for triple in triples[:4])
                blocks.append("\n".join(lines))
        return blocks

    probes = {key: probe for key, *_, probe in UNITS}
    for name, (_, allowed) in READERS.items():
        allowed_ids = [dataset_ids[key] for key in allowed]
        own_probe = probes[allowed[-1]]
        found = await recall(users[name], own_probe, allowed_ids)
        foreign = [c for key, _, _, canaries, _ in UNITS if key not in allowed for c in canaries]
        check(
            f"{name} receives only allowed facts",
            (not found["denied"]) and bool(hits(found["text"], [own_probe])) and not hits(found["text"], foreign),
            f"probe={own_probe} own_hit={bool(hits(found['text'], [own_probe]))} foreign={hits(found['text'], foreign) or 'none'} datasets={found['datasets']}",
        )
        forbidden = next(key for key, *_ in UNITS if key not in allowed) if name != "director" else None
        if forbidden:
            denied = await recall(users[name], probes[forbidden], [dataset_ids[forbidden]])
            check(
                f"{name} is denied {forbidden}",
                denied["denied"],
                denied["error"] or "no error",
            )

    employee_pay = await recall(users["employee"], "EUR 185,000", [dataset_ids["people"]])
    check(
        "an employee is denied the people dataset",
        employee_pay["denied"],
        employee_pay["error"] or "no error",
    )
    people_board = await recall(users["people"], "14 roles", [dataset_ids["board"]])
    check(
        "the people team is denied the board dataset",
        people_board["denied"],
        people_board["error"] or "no error",
    )
    finance_board = await recall(users["finance"], "165 million", [dataset_ids["board"]])
    check(
        "the finance team is denied the board term sheet",
        finance_board["denied"],
        finance_board["error"] or "no error",
    )
    board_eng = await recall(users["board"], "KESTREL", [dataset_ids["engineering"]])
    check(
        "the board is denied the engineering dataset",
        board_eng["denied"],
        board_eng["error"] or "no error",
    )
    party = await recall(users["employee"], "summer party", [dataset_ids["company"]])
    check(
        "an employee can read the company summer party",
        (not party["denied"]) and bool(hits(party["text"], ["summer party"])),
        f"datasets={party['datasets']}",
    )

    people_blocks = neighborhood_for(READERS["people"][1])
    people_names = [block.split("\n", 1)[0] for block in people_blocks]
    check(
        "people neighborhood includes Sofia and leaves the other graphs closed",
        any(name == "same_entity: sofia brandt" for name in people_names)
        and all("medrava" not in name and "kirkwall" not in name and "lukas" not in name for name in people_names),
        ", ".join(people_names) or "none",
    )
    director_blocks = neighborhood_for(READERS["director"][1])
    check(
        "director neighborhood joins every shared entity",
        len(director_blocks) == len(links) and len(links) >= 4,
        f"{len(director_blocks)} neighborhoods",
    )

    await authorized_revoke_permission_on_datasets(users["director"].id, [dataset_ids["legal"]], "read", admin.id)
    after = await recall(users["director"], "LGL-2231", [dataset_ids["legal"]])
    check(
        "after revoke the legal dataset stays closed for the director",
        after["denied"],
        after["error"] or f"datasets={after['datasets']}",
    )
    still = await recall(users["director"], "Quillstream", [dataset_ids["board"]])
    check(
        "after the legal revoke the director can still read the board dataset",
        (not still["denied"]) and bool(hits(still["text"], ["Quillstream"])),
        f"denied={still['denied']} datasets={still['datasets']}",
    )
    await authorized_give_permission_on_datasets(users["director"].id, [dataset_ids["legal"]], "read", admin.id)

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Structured Brightmoor Q3 2026 report",
        "",
        "Dispatcher followed `.cursor/skills/dispatcher/SKILL.md` and `.cursor/skills/dispatcher/RULES.md`.",
        "Each section already names one audience. The section was labeled and stored whole.",
        "The mixed source was never passed to `remember()`.",
        "These datasets are separate from the earlier Brightmoor graphs.",
        "",
        "Audiences: company_general, board_confidential, finance_confidential, people_confidential, gtm_confidential, engineering_internal, security_confidential, legal_confidential.",
        "",
        f"Result: {passed}/{len(checks)} checks passed.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        safe = detail.replace("|", "/")
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {safe} |")
    lines.extend(["", "## Neighborhoods for a reader of every dataset", ""])
    for block in director_blocks:
        lines.extend(["```", block, "```", ""])
    lines.extend([
        "The neighborhood is built for this question only. It is not written back with `remember()`.",
        "",
    ])
    REPORT.write_text("\n".join(lines))
    print(f"\n{passed}/{len(checks)} written to {REPORT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
