"""
Store two already-separated Keel files and answer from the retrieval.

HR and finance are named before remember(). A shared employee number is
retrieved by Cognee once per dataset. Dispatcher keeps the facts the question
asks for and names the dataset each fact came from.
"""

import asyncio
import json
import re
import sys
from uuid import UUID, uuid4

import poc_config as cfg

import cognee
import ladybug
from cognee.modules.data.methods.get_datasets_by_name import get_datasets_by_name
from cognee.modules.search.types import SearchType
from cognee.modules.users.exceptions import PermissionDeniedError
from cognee.modules.users.methods import create_user, get_user_by_email
from cognee.modules.users.permissions.methods import authorized_give_permission_on_datasets
from fastapi_users.exceptions import UserAlreadyExists

ORG = "keel"
FILES = {
    "hr": cfg.ROOT / "data" / "keel" / "hr.txt",
    "finance": cfg.ROOT / "data" / "keel" / "finance.txt",
}
DATASETS = {key: f"{ORG}_{key}" for key in FILES}
CANARIES = {
    "hr": ["band H5", "19 days"],
    "finance": ["EXP-1188", "EUR 4,800", "CC-42"],
}
COMMON = "EMP-3304"
READERS = {
    "hr": "hr.user@keel.poc",
    "finance": "finance.user@keel.poc",
    "both": "hr.finance.user@keel.poc",
}
GRANTS = {"hr": ["hr"], "finance": ["finance"], "both": ["hr", "finance"]}
OWNER_EMAIL = "keel.admin@keel.poc"
ACCESS_MAP = cfg.RESULTS_DIR / "keel_access_map.txt"
MANIFEST = cfg.RESULTS_DIR / "keel_manifest.txt"
REPORT = cfg.RESULTS_DIR / "keel_skill_test.md"
LINKS = cfg.RESULTS_DIR / "keel_links.json"
NO_ACCESS = "You do not have access."
NOT_IN = "That is not in the information you can access."
OWNER_REFUSAL = "Questions run as a reader. The owner is not used to answer."
NAME = {"ravi", "mendis"}
GENERIC = {"employee", "number", "expense", "record", "department", "dataset", "person", "submit"}
STOP = {"what", "does", "have", "about", "know", "this", "that", "with", "from", "your", "did", "the", "and"}


def question_tokens(question):
    found = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", question.lower()))
    tokens = {token for token in found if token not in STOP and (len(token) > 3 or "-" in token or any(ch.isdigit() for ch in token))}
    codes = {token for token in tokens if "-" in token or any(ch.isdigit() for ch in token)}
    if codes:
        return codes
    return (tokens - NAME - GENERIC) or tokens


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.])\s+", text) if part.strip()]


def needed(question, text):
    tokens = question_tokens(question)
    kept = [sentence for sentence in sentences(text) if any(token in sentence.lower() for token in tokens)]
    return " ".join(kept)


def answer_from(question, retrieved):
    parts = []
    used = []
    for name, text in retrieved:
        sentence = needed(question, text or "")
        if sentence:
            parts.append(f"In {name}, the retrieved record says: {sentence}")
            used.append(name)
    if not parts:
        return "none", NOT_IN, []
    mode = "direct" if len(parts) == 1 else "combined"
    return mode, " ".join(parts), used


def result_text(result):
    if isinstance(result, dict):
        for key in ("text", "search_result", "context_result", "context"):
            value = result.get(key)
            if value:
                return str(value)
        return ""
    for attr in ("text", "search_result", "context"):
        value = getattr(result, attr, None)
        if value:
            return str(value)
    return str(result)


def result_dataset(result):
    if isinstance(result, dict):
        return result.get("dataset_name")
    return getattr(result, "dataset_name", None)


async def principal(email):
    try:
        user = await create_user(email, cfg.PASSWORD, is_superuser=False)
    except UserAlreadyExists:
        user = await get_user_by_email(email)
    return user


async def retrieve(user, question, dataset_ids):
    try:
        results = await cognee.recall(
            question,
            query_type=SearchType.CHUNKS_LEXICAL,
            user=user,
            dataset_ids=dataset_ids,
            auto_route=False,
            only_context=True,
            top_k=8,
        )
    except PermissionDeniedError as error:
        return {"denied": True, "by_dataset": {}, "error": str(error), "opened": []}
    by_dataset = {}
    for result in results or []:
        name = result_dataset(result) or "unknown"
        text = result_text(result)
        if text.strip():
            by_dataset[str(name)] = text
    return {"denied": False, "by_dataset": by_dataset, "error": None, "opened": list(by_dataset)}


def names_closed(question, closed_ids, id_to_name):
    low = question.lower()
    for dataset_id in closed_ids:
        dataset_name = id_to_name.get(dataset_id)
        if not dataset_name:
            continue
        audience = dataset_name.split("_", 1)[-1]
        if re.search(rf"\b{re.escape(dataset_name)}\b", low) or re.search(rf"\b{re.escape(audience)}\b", low):
            return True
    return False


async def ask(user, owner, question, requested_ids, allowed_ids, id_to_name):
    """Search the open datasets. A closed id is removed before recall."""
    if user.id == owner.id:
        return {"recalled": False, "by_dataset": {}, "opened": [], "answer": OWNER_REFUSAL, "mode": "owner"}
    allowed = set(allowed_ids)
    open_ids = [dataset_id for dataset_id in requested_ids if dataset_id in allowed]
    closed_ids = [dataset_id for dataset_id in requested_ids if dataset_id not in allowed]
    retrieved = await retrieve(user, question, open_ids) if open_ids else {"denied": False, "by_dataset": {}}
    if retrieved.get("denied"):
        retrieved = {"denied": True, "by_dataset": {}}
    mode, body, used = answer_from(question, list(retrieved["by_dataset"].items()))
    named = names_closed(question, closed_ids, id_to_name)
    if closed_ids and (not open_ids or named):
        if not open_ids or mode == "none":
            body = NO_ACCESS
            mode = "closed"
            used = []
        else:
            body = f"{NO_ACCESS} {body}"
    return {
        "recalled": bool(open_ids) and not retrieved.get("denied"),
        "by_dataset": retrieved["by_dataset"],
        "opened": used,
        "answer": body,
        "mode": mode,
    }


def matching_entity(graph_path, needle):
    connection = ladybug.Connection(ladybug.Database(str(graph_path), read_only=True))
    nodes = connection.execute(
        "MATCH (n:Node {type: 'Entity'}) WHERE n.name CONTAINS $needle RETURN n.id, n.name",
        {"needle": needle},
    ).get_all()
    if not nodes:
        return None
    return str(nodes[0][0])


async def main():
    cfg.configure_cognee()
    cfg.RESULTS_DIR.mkdir(exist_ok=True)
    checks = []

    def check(name, passed, detail):
        checks.append((name, passed, detail))
        print(f"[{'PASS' if passed else 'FAIL'}] {name} — {detail}", flush=True)

    texts = {key: path.read_text() for key, path in FILES.items()}
    for key, own in CANARIES.items():
        foreign = [item for other, canaries in CANARIES.items() if other != key for item in canaries]
        leaked = [item for item in foreign if item.lower() in texts[key].lower()]
        present = COMMON in texts[key] and all(item in texts[key] for item in own)
        check(f"{key} file is one department and shares {COMMON}", not leaked and present, "clean" if not leaked else str(leaked))

    ACCESS_MAP.write_text(
        "\n".join(
            [
                "organization: keel",
                f"owner: {OWNER_EMAIL}",
                "owner is not a superuser",
                "access control: on",
                "There is no director and no superuser.",
                "The dataset is named before ingestion.",
                "",
                "domain: hr",
                "dataset: keel_hr",
                "read: hr.user@keel.poc, hr.finance.user@keel.poc",
                "",
                "domain: finance",
                "dataset: keel_finance",
                "read: finance.user@keel.poc, hr.finance.user@keel.poc",
                "",
            ]
        )
    )
    MANIFEST.write_text(
        "\n".join(
            f"source: {FILES[key].name}\ndataset: {DATASETS[key]}\ncanaries: {COMMON}, {', '.join(CANARIES[key])}\n"
            for key in FILES
        )
    )

    owner = await principal(OWNER_EMAIL)
    check("owner is not a superuser", owner.is_superuser is False, owner.email)
    users = {name: await principal(email) for name, email in READERS.items()}
    for name, user in users.items():
        check(f"{name} reader is not a superuser", user.is_superuser is False, user.email)

    dataset_ids = {}
    if "--query-only" in sys.argv:
        found = await get_datasets_by_name(list(DATASETS.values()), owner.id)
        by_name = {dataset.name: dataset.id for dataset in found}
        for key, name in DATASETS.items():
            dataset_ids[key] = UUID(str(by_name[name]))
    else:
        for key, path in FILES.items():
            print(f"Ingesting {path.name} into {DATASETS[key]} ...", flush=True)
            result = await cognee.remember(
                [str(path)],
                dataset_name=DATASETS[key],
                user=owner,
                self_improvement=False,
            )
            dataset_ids[key] = UUID(str(result.dataset_id))
        for name, keys in GRANTS.items():
            await authorized_give_permission_on_datasets(
                users[name].id, [dataset_ids[key] for key in keys], "read", owner.id
            )

    admin_dir = cfg.SYSTEM_ROOT / "databases" / str(owner.id)
    link = {
        "name": "ravi mendis",
        "kind": "person",
        "datasets": {},
        "same_id_is_not_an_edge": True,
    }
    for key, dataset_name in DATASETS.items():
        entity_id = matching_entity(admin_dir / f"{dataset_ids[key]}.lbug", "ravi")
        if entity_id:
            link["datasets"][dataset_name] = entity_id
    same_id = len(set(link["datasets"].values())) == 1 and len(link["datasets"]) == 2
    LINKS.write_text(json.dumps([link] if len(link["datasets"]) >= 2 else [], indent=2) + "\n")
    check(
        "the shared entity id is recorded as two nodes",
        same_id and link["same_id_is_not_an_edge"] is True,
        next(iter(link["datasets"].values()), "missing"),
    )

    allowed = {
        "hr": [dataset_ids["hr"]],
        "finance": [dataset_ids["finance"]],
        "both": [dataset_ids["hr"], dataset_ids["finance"]],
    }
    id_to_name = {dataset_ids[key]: DATASETS[key] for key in DATASETS}
    closed = await ask(users["hr"], owner, "What does finance know about EXP-1188?", [dataset_ids["finance"]], allowed["hr"], id_to_name)
    check(
        "hr person is denied the finance dataset",
        closed["answer"] == NO_ACCESS and "EXP-1188" not in closed["answer"] and closed["opened"] == [],
        closed["answer"],
    )

    missing = await ask(
        users["hr"], owner, "What expense EXP-1188 did Ravi Mendis submit?", [dataset_ids["hr"]], allowed["hr"], id_to_name
    )
    check(
        "hr person does not receive the finance expense from the people file",
        missing["mode"] == "none" and missing["answer"] == NOT_IN,
        missing["answer"],
    )

    number_question = "What is Ravi Mendis's employee number EMP-3304?"
    number = await ask(users["finance"], owner, number_question, [dataset_ids["finance"]], allowed["finance"], id_to_name)
    check(
        "one dataset is trimmed to the employee number",
        number["mode"] == "direct"
        and COMMON in number["answer"]
        and "EXP-1188" not in number["answer"]
        and "EUR 4,800" not in number["answer"]
        and "Keel payments record" not in number["answer"],
        number["answer"],
    )

    mixed = await ask(
        users["hr"],
        owner,
        number_question,
        [dataset_ids["hr"], dataset_ids["finance"]],
        allowed["hr"],
        id_to_name,
    )
    check(
        "a closed dataset does not cancel the open dataset",
        NO_ACCESS not in mixed["answer"]
        and COMMON in mixed["answer"]
        and "EXP-1188" not in mixed["answer"]
        and mixed["opened"] == ["keel_hr"],
        mixed["answer"],
    )
    named = await ask(
        users["hr"],
        owner,
        "What does the finance dataset say about EMP-3304?",
        [dataset_ids["hr"], dataset_ids["finance"]],
        allowed["hr"],
        id_to_name,
    )
    check(
        "naming finance denies that dataset and still answers from people",
        named["answer"].startswith(NO_ACCESS)
        and COMMON in named["answer"]
        and "EXP-1188" not in named["answer"]
        and named["opened"] == ["keel_hr"],
        named["answer"],
    )

    raw_denied = await retrieve(users["hr"], number_question, [dataset_ids["hr"], dataset_ids["finance"]])
    check(
        "cognee refuses the whole call when a closed dataset is included",
        raw_denied["denied"] is True,
        raw_denied["error"] or "no error",
    )

    question = "What is Ravi Mendis's employee number EMP-3304, and what expense EXP-1188 did Ravi Mendis submit?"
    stale = uuid4()
    both = await ask(
        users["both"], owner, question, [dataset_ids["hr"], dataset_ids["finance"], stale], allowed["both"], id_to_name
    )
    check(
        "cognee returns the shared employee number from both datasets",
        set(both["by_dataset"]) == {"keel_hr", "keel_finance"} and all(COMMON in text for text in both["by_dataset"].values()),
        ", ".join(sorted(both["by_dataset"])),
    )
    combined = both["answer"]
    check(
        "dispatcher keeps the shared number and the finance expense",
        both["mode"] == "combined"
        and set(both["opened"]) == {"keel_hr", "keel_finance"}
        and NO_ACCESS not in combined
        and "keel_hr" in combined
        and "keel_finance" in combined
        and COMMON in combined
        and "EXP-1188" in combined
        and "band H5" not in combined
        and "19 days" not in combined,
        f"mode={both['mode']}",
    )

    finance_only = await ask(users["finance"], owner, question, [dataset_ids["finance"]], allowed["finance"], id_to_name)
    check(
        "finance person receives only the finance sentences the question asks for",
        finance_only["mode"] == "direct"
        and finance_only["opened"] == ["keel_finance"]
        and "EXP-1188" in finance_only["answer"]
        and COMMON in finance_only["answer"]
        and "band H5" not in finance_only["answer"]
        and "Keel payments record" not in finance_only["answer"],
        finance_only["answer"],
    )

    owner_ask = await ask(owner, owner, question, [dataset_ids["hr"], dataset_ids["finance"]], allowed["both"], id_to_name)
    check(
        "the owner is not used to answer",
        owner_ask["recalled"] is False and owner_ask["answer"] == OWNER_REFUSAL,
        owner_ask["answer"],
    )

    def block(title, by_dataset):
        lines = [f"### {title}", ""]
        for name in ("keel_hr", "keel_finance"):
            text = by_dataset.get(name)
            if text:
                lines.extend([f"`{name}`", "", text.strip(), ""])
        if not by_dataset:
            lines.extend(["No dataset was opened.", ""])
        return lines

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Keel HR and finance",
        "",
        "Two files were stored in the datasets named before ingestion: `keel_hr` and `keel_finance`.",
        f"Both files contain {COMMON} for Ravi Mendis. HR also has band H5 and 19 days of leave. Finance also has expense EXP-1188.",
        "",
        "## Cognee retrieval for the person who can read both",
        "",
        "Cognee searched each graph on its own and returned one result per dataset.",
        "",
        *block("Raw result", both["by_dataset"]),
        "## Dispatcher answer",
        "",
        combined,
        "",
        "## Finance person asks only for the employee number",
        "",
        number["answer"],
        "",
        "## HR person asks for the number while finance is also listed",
        "",
        mixed["answer"],
        "",
        "## HR person names finance and asks for the employee number",
        "",
        named["answer"],
        "",
        "## HR person asks for the finance dataset",
        "",
        closed["answer"],
        "",
        "## HR person asks for the expense inside the people dataset",
        "",
        missing["answer"],
        "",
        "## Finance person asks for the number and the expense",
        "",
        finance_only["answer"],
        "",
        "## Owner asks the same question",
        "",
        owner_ask["answer"],
        "",
        f"## Checks: {passed}/{len(checks)}",
        "",
    ]
    for name, ok, detail in checks:
        lines.append(f"- {'PASS' if ok else 'FAIL'}: {name} — {detail}")
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"\n{passed}/{len(checks)} written to {REPORT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
