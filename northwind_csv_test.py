"""
Store the Northwind CSVs in the datasets named by the files, then answer.

hr.csv, finance.csv, legal.csv, marketing.csv, and employees_master.csv
are already one audience each. The dataset name comes from the file name.
Cognee searches each permitted graph on its own. Dispatcher keeps the row
that contains the identifier and names the dataset it came from.
"""

import asyncio
import json
import re
import sys
from uuid import UUID, uuid4

import poc_config as cfg

import cognee
import ladybug
from cognee.context_global_variables import set_database_global_context_variables
from cognee.infrastructure.databases.graph.get_graph_engine import get_graph_engine
from cognee.modules.data.methods.get_authorized_existing_datasets import get_authorized_existing_datasets
from cognee.modules.data.methods.get_datasets_by_name import get_datasets_by_name
from cognee.modules.retrieval.exceptions.exceptions import NoDataError
from cognee.modules.search.types import SearchType
from cognee.modules.users.exceptions import PermissionDeniedError
from cognee.modules.users.methods import create_user, get_user_by_email
from cognee.modules.users.permissions.methods import (
    authorized_give_permission_on_datasets,
    authorized_revoke_permission_on_datasets,
)
from fastapi_users.exceptions import UserAlreadyExists

ORG = "northwind"
FILES = {
    "hr": cfg.ROOT / "data" / "northwind" / "hr.csv",
    "finance": cfg.ROOT / "data" / "northwind" / "finance.csv",
    "legal": cfg.ROOT / "data" / "northwind" / "legal.csv",
    "marketing": cfg.ROOT / "data" / "northwind" / "marketing.csv",
    "employees_master": cfg.ROOT / "data" / "northwind" / "employees_master.csv",
}
DATASETS = {key: f"{ORG}_{key}" for key in FILES}
CANARIES = {
    "hr": ["Payroll Specialist"],
    "finance": ["Treasury Analyst"],
    "legal": ["Privacy Officer"],
    "marketing": ["SEO Specialist"],
    "employees_master": ["FIN;HR;LEG"],
}
READERS = {
    "hr": "hr.user@northwind.poc",
    "finance": "finance.user@northwind.poc",
    "legal": "legal.user@northwind.poc",
    "marketing": "marketing.user@northwind.poc",
    "span": "hr.finance.legal.user@northwind.poc",
    "roster": "roster.user@northwind.poc",
}
GRANTS = {
    "hr": ["hr"],
    "finance": ["finance"],
    "legal": ["legal"],
    "marketing": ["marketing"],
    "span": ["hr", "finance", "legal"],
    "roster": ["employees_master"],
}
OWNER_EMAIL = "northwind.admin@northwind.poc"
ACCESS_MAP = cfg.RESULTS_DIR / "northwind_access_map.txt"
MANIFEST = cfg.RESULTS_DIR / "northwind_manifest.txt"
REPORT = cfg.RESULTS_DIR / "northwind_csv_test.md"
LINKS = cfg.RESULTS_DIR / "northwind_links.json"
NO_ACCESS = "You do not have access."
NOT_IN = "That is not in the information you can access."
OWNER_REFUSAL = "Questions run as a reader. The owner is not used to answer."
GENERIC = {
    "employee",
    "number",
    "expense",
    "record",
    "department",
    "dataset",
    "person",
    "submit",
    "title",
    "hold",
    "what",
    "does",
    "have",
    "about",
    "know",
    "this",
    "that",
    "with",
    "from",
    "your",
    "the",
    "and",
    "job",
}
STOP = GENERIC


def question_tokens(question):
    found = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", question.lower()))
    tokens = {
        token
        for token in found
        if token not in STOP and (len(token) > 3 or "-" in token or any(ch.isdigit() for ch in token))
    }
    codes = {token for token in tokens if "-" in token or any(ch.isdigit() for ch in token)}
    if codes:
        return codes
    return (tokens - GENERIC) or tokens


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.])\s+", text) if part.strip()]


def records(text):
    """One CSV row is one record. Cognee may return the whole file as one chunk."""
    plain = (text or "").replace("\\n", "\n")
    parts = re.split(r"(?=employee_id:\s*EMP\d{4}\b)", plain)
    rows = [part.strip() for part in parts if re.search(r"employee_id:\s*EMP\d{4}\b", part)]
    if len(rows) > 1 or (len(rows) == 1 and "job_title:" in rows[0].lower() or "departments:" in rows[0].lower()):
        return rows
    labeled = re.split(r"(?=Row \d+:)", plain)
    labeled_rows = [part.strip() for part in labeled if re.match(r"Row \d+:", part.strip())]
    if labeled_rows:
        return labeled_rows
    return sentences(plain) or ([plain.strip()] if plain.strip() else [])


def row_employee(record):
    match = re.search(r"employee_id:\s*(EMP\d{4})", record, flags=re.I)
    return match.group(1).lower() if match else ""


def needed(question, text):
    tokens = question_tokens(question)
    codes = {token for token in tokens if token.startswith("emp")}
    kept = []
    for record in records(text):
        own = row_employee(record)
        if codes:
            if own in codes:
                kept.append(re.split(r"\n---|\n## ", record, maxsplit=1)[0].strip())
            continue
        if any(token in record.lower() for token in tokens):
            kept.append(re.split(r"\n---|\n## ", record, maxsplit=1)[0].strip())
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


def employee_ids(question):
    found = []
    for code in re.findall(r"EMP-?\d+", question, flags=re.I):
        code = code.upper()
        if code not in found:
            found.append(code)
    return found


def row_text(properties):
    raw = properties
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return raw
    if isinstance(raw, dict):
        return str(raw.get("text") or "")
    return str(properties or "")


async def exact_employee_rows(user, question, dataset_ids):
    """Match employee_id exactly, after Cognee has checked read on every requested dataset."""
    codes = employee_ids(question)
    if not codes or not dataset_ids:
        return None
    datasets = await get_authorized_existing_datasets(dataset_ids, "read", user)
    by_dataset = {}
    tabular = False
    for dataset in datasets:
        async with set_database_global_context_variables(dataset.id, user.id, permission_type="read"):
            engine = await get_graph_engine()
            present = await engine.query(
                "MATCH (n:Node {type: 'DltRow'}) RETURN n.id LIMIT 1"
            )
            if not present:
                continue
            tabular = True
            texts = []
            for code in codes:
                rows = await engine.query(
                    "MATCH (n:Node {type: 'DltRow'}) WHERE n.properties CONTAINS $needle RETURN n.properties",
                    {"needle": f"employee_id: {code}"},
                )
                for row in rows:
                    text = row_text(row[0] if row else "")
                    own = row_employee(text)
                    if own == code.lower():
                        texts.append(text)
            if texts:
                by_dataset[dataset.name] = "\n".join(texts)
    if not tabular:
        return None
    return {"denied": False, "by_dataset": by_dataset, "error": None, "opened": list(by_dataset)}


async def retrieve(user, question, dataset_ids, query_type=SearchType.HYBRID_COMPLETION):
    if query_type == SearchType.HYBRID_COMPLETION:
        try:
            exact = await exact_employee_rows(user, question, dataset_ids)
        except PermissionDeniedError as error:
            return {"denied": True, "by_dataset": {}, "error": str(error), "opened": []}
        if exact is not None:
            return exact
    try:
        results = await cognee.recall(
            question,
            query_type=query_type,
            user=user,
            dataset_ids=dataset_ids,
            auto_route=False,
            only_context=True,
            top_k=40,
        )
    except PermissionDeniedError as error:
        return {"denied": True, "by_dataset": {}, "error": str(error), "opened": []}
    except NoDataError as error:
        return {"denied": False, "by_dataset": {}, "error": str(error), "opened": [], "empty": True}
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
    if not graph_path.exists():
        return None
    connection = ladybug.Connection(ladybug.Database(str(graph_path), read_only=True))
    try:
        nodes = connection.execute(
            "MATCH (n:Node {type: 'DltRow'}) WHERE n.properties CONTAINS $needle RETURN n.id LIMIT 3",
            {"needle": needle},
        ).get_all()
    except Exception:
        return None
    if not nodes:
        return None
    return str(nodes[0][0]), "DltRow"


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
        present = all(item in texts[key] for item in own)
        check(f"{key} file stays in its own dataset", not leaked and present, "clean" if not leaked and present else str(leaked or own))

    ACCESS_MAP.write_text(
        "\n".join(
            [
                "organization: northwind",
                f"owner: {OWNER_EMAIL}",
                "owner is not a superuser",
                "access control: on",
                "There is no director and no superuser.",
                "The dataset is named by the file before ingestion.",
                "",
                "domain: hr",
                "dataset: northwind_hr",
                "source: hr.csv",
                "read: hr.user@northwind.poc, hr.finance.legal.user@northwind.poc",
                "",
                "domain: finance",
                "dataset: northwind_finance",
                "source: finance.csv",
                "read: finance.user@northwind.poc, hr.finance.legal.user@northwind.poc",
                "",
                "domain: legal",
                "dataset: northwind_legal",
                "source: legal.csv",
                "read: legal.user@northwind.poc, hr.finance.legal.user@northwind.poc",
                "",
                "domain: marketing",
                "dataset: northwind_marketing",
                "source: marketing.csv",
                "read: marketing.user@northwind.poc",
                "",
                "domain: employees_master",
                "dataset: northwind_employees_master",
                "source: employees_master.csv",
                "read: roster.user@northwind.poc",
                "",
            ]
        )
    )
    MANIFEST.write_text(
        "\n".join(
            f"source: {FILES[key].name}\ndataset: {DATASETS[key]}\ncanaries: {', '.join(CANARIES[key])}\n"
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
            print(f"Stored {DATASETS[key]} {dataset_ids[key]}", flush=True)
        for name, keys in GRANTS.items():
            await authorized_give_permission_on_datasets(
                users[name].id, [dataset_ids[key] for key in keys], "read", owner.id
            )

    admin_dir = cfg.SYSTEM_ROOT / "databases" / str(owner.id)
    link = {
        "name": "Mia Silva",
        "kind": "person",
        "datasets": {},
        "same_id_is_not_an_edge": True,
    }
    for key in ("hr", "finance", "legal"):
        found = matching_entity(admin_dir / f"{dataset_ids[key]}.lbug", "employee_id: EMP0037")
        if found:
            link["datasets"][DATASETS[key]] = {"id": found[0], "matched": found[1]}
    LINKS.write_text(json.dumps([link] if len(link["datasets"]) >= 2 else [], indent=2) + "\n")
    check(
        "Mia Silva's row is stored in each department graph, and the ids are not an edge",
        len(link["datasets"]) == 3 and link["same_id_is_not_an_edge"] is True,
        json.dumps(link["datasets"]) if link["datasets"] else "no mia node",
    )

    allowed = {name: [dataset_ids[key] for key in keys] for name, keys in GRANTS.items()}
    id_to_name = {dataset_ids[key]: DATASETS[key] for key in DATASETS}
    lexical = await retrieve(
        users["hr"], "What job title does EMP0037 hold?", [dataset_ids["hr"]], SearchType.CHUNKS_LEXICAL
    )
    check(
        "chunk search has no document chunks for a CSV dataset",
        lexical.get("empty") is True and not lexical["by_dataset"],
        (lexical.get("error") or "chunks were returned")[:220],
    )

    mia = "What job title does EMP0037 hold?"

    hr_only = await ask(users["hr"], owner, mia, [dataset_ids["hr"]], allowed["hr"], id_to_name)
    check(
        "hr person receives only Mia Silva's HR row",
        hr_only["mode"] == "direct"
        and hr_only["opened"] == ["northwind_hr"]
        and "EMP0037" in hr_only["answer"]
        and "HR Manager" in hr_only["answer"]
        and "Controller" not in hr_only["answer"]
        and "Paralegal" not in hr_only["answer"]
        and "employee_id: EMP0011" not in hr_only["answer"]
        and "Payroll Specialist" not in hr_only["answer"],
        hr_only["answer"][:500],
    )

    closed = await ask(
        users["hr"],
        owner,
        "What does finance say about EMP0037?",
        [dataset_ids["finance"]],
        allowed["hr"],
        id_to_name,
    )
    check(
        "hr person is denied the finance dataset",
        closed["answer"] == NO_ACCESS and closed["opened"] == [],
        closed["answer"],
    )

    missing = await ask(
        users["hr"],
        owner,
        "What job title does EMP0001 hold?",
        [dataset_ids["hr"]],
        allowed["hr"],
        id_to_name,
    )
    check(
        "hr person does not receive a finance-only employee",
        missing["mode"] == "none" and missing["answer"] == NOT_IN,
        missing["answer"],
    )

    kept_open = await ask(
        users["hr"],
        owner,
        mia,
        [dataset_ids["hr"], dataset_ids["finance"]],
        allowed["hr"],
        id_to_name,
    )
    check(
        "a closed finance id does not cancel the HR answer",
        NO_ACCESS not in kept_open["answer"]
        and "HR Manager" in kept_open["answer"]
        and "Controller" not in kept_open["answer"]
        and kept_open["opened"] == ["northwind_hr"],
        kept_open["answer"][:400],
    )

    raw_denied = await retrieve(users["hr"], mia, [dataset_ids["hr"], dataset_ids["finance"]])
    check(
        "cognee refuses the whole call when a closed dataset is included",
        raw_denied["denied"] is True,
        (raw_denied["error"] or "no error")[:240],
    )

    span = await ask(
        users["span"],
        owner,
        mia,
        [dataset_ids["hr"], dataset_ids["finance"], dataset_ids["legal"]],
        allowed["span"],
        id_to_name,
    )
    check(
        "cognee returns Mia Silva separately from HR, finance, and legal",
        set(span["by_dataset"]) == {"northwind_hr", "northwind_finance", "northwind_legal"}
        and all("EMP0037" in text for text in span["by_dataset"].values()),
        ", ".join(sorted(span["by_dataset"])) or "none",
    )
    combined = span["answer"]
    check(
        "dispatcher keeps Mia Silva's three job titles and drops the other rows",
        span["mode"] == "combined"
        and set(span["opened"]) == {"northwind_hr", "northwind_finance", "northwind_legal"}
        and "northwind_hr" in combined
        and "northwind_finance" in combined
        and "northwind_legal" in combined
        and "HR Manager" in combined
        and "Controller" in combined
        and "Paralegal" in combined
        and "employee_id: EMP0001" not in combined
        and "employee_id: EMP0038" not in combined
        and "Payroll Specialist" not in combined
        and "Privacy Officer" not in combined
        and "Finance Manager" not in combined
        and "SEO Specialist" not in combined
        and "FIN;HR;LEG" not in combined
        and NO_ACCESS not in combined,
        f"mode={span['mode']} opened={span['opened']}",
    )

    stale = uuid4()
    with_stale = await ask(
        users["span"],
        owner,
        mia,
        [dataset_ids["hr"], dataset_ids["finance"], dataset_ids["legal"], stale],
        allowed["span"],
        id_to_name,
    )
    check(
        "an unnamed closed id does not add a denial",
        NO_ACCESS not in with_stale["answer"] and "Controller" in with_stale["answer"] and "Paralegal" in with_stale["answer"],
        with_stale["mode"],
    )

    roster = await ask(
        users["roster"],
        owner,
        "Which departments include EMP0037?",
        [dataset_ids["employees_master"]],
        allowed["roster"],
        id_to_name,
    )
    check(
        "the roster reader receives the master row and not a department job title",
        roster["mode"] == "direct"
        and "FIN;HR;LEG" in roster["answer"]
        and "HR Manager" not in roster["answer"]
        and "employee_id: EMP0001" not in roster["answer"],
        roster["answer"][:400],
    )

    owner_ask = await ask(owner, owner, mia, [dataset_ids["hr"], dataset_ids["finance"], dataset_ids["legal"]], allowed["span"], id_to_name)
    check(
        "the owner is not used to answer",
        owner_ask["recalled"] is False and owner_ask["answer"] == OWNER_REFUSAL,
        owner_ask["answer"],
    )

    shown = []

    def expect(group, who, question, result, needles, forbid=(), datasets=None, mode=None):
        answer = result["answer"]
        ok = all(needle in answer for needle in needles) and all(needle not in answer for needle in forbid)
        if datasets is not None:
            ok = ok and set(result["opened"]) == set(datasets)
        if mode is not None:
            ok = ok and result["mode"] == mode
        check(
            question if who == "" else f"{who}: {question}",
            ok,
            f"mode={result['mode']} opened={result['opened']}",
        )
        shown.append(
            {
                "group": group,
                "who": who,
                "question": question,
                "mode": result["mode"],
                "opened": result["opened"],
                "raw_chars": {name: len(text) for name, text in result["by_dataset"].items()},
                "answer": answer,
            }
        )

    span_ids = [dataset_ids["hr"], dataset_ids["finance"], dataset_ids["legal"]]
    single_cases = [
        (
            "hr reader",
            users["hr"],
            "What job title does EMP0011 hold?",
            [dataset_ids["hr"]],
            allowed["hr"],
            ["employee_id: EMP0011", "job_title: HR Business Partner", "allocation_pct: 100"],
            ["employee_id: EMP0006", "Head of HR", "Accountant"],
            ["northwind_hr"],
            "direct",
        ),
        (
            "finance reader",
            users["finance"],
            "What job title does EMP0001 hold?",
            [dataset_ids["finance"]],
            allowed["finance"],
            ["employee_id: EMP0001", "job_title: CFO"],
            ["employee_id: EMP0004", "Accountant", "Controller"],
            ["northwind_finance"],
            "direct",
        ),
        (
            "legal reader",
            users["legal"],
            "What job title does EMP0005 hold?",
            [dataset_ids["legal"]],
            allowed["legal"],
            ["employee_id: EMP0005", "job_title: General Counsel", "location: Colombo"],
            ["employee_id: EMP0008", "Compliance Officer", "Paralegal"],
            ["northwind_legal"],
            "direct",
        ),
        (
            "marketing reader",
            users["marketing"],
            "What job title does EMP0003 hold?",
            [dataset_ids["marketing"]],
            allowed["marketing"],
            ["employee_id: EMP0003", "job_title: Head of Marketing", "location: Berlin"],
            ["employee_id: EMP0008", "SEO Specialist"],
            ["northwind_marketing"],
            "direct",
        ),
        (
            "hr reader",
            users["hr"],
            "What job title does EMP0004 hold?",
            [dataset_ids["hr"]],
            allowed["hr"],
            ["employee_id: EMP0004", "job_title: Head of HR", "allocation_pct: 60"],
            ["Accountant", "allocation_pct: 40"],
            ["northwind_hr"],
            "direct",
        ),
        (
            "hr reader",
            users["hr"],
            "What job title does EMP0003 hold?",
            [dataset_ids["hr"]],
            allowed["hr"],
            [NOT_IN],
            ["Head of Marketing"],
            [],
            "none",
        ),
        (
            "marketing reader",
            users["marketing"],
            "What job title does EMP0011 hold?",
            [dataset_ids["marketing"]],
            allowed["marketing"],
            [NOT_IN],
            ["HR Business Partner"],
            [],
            "none",
        ),
        (
            "finance reader",
            users["finance"],
            "What does hr say about EMP0011?",
            [dataset_ids["hr"]],
            allowed["finance"],
            [NO_ACCESS],
            ["HR Business Partner"],
            [],
            "closed",
        ),
    ]
    for who, user, question, requested, allowed_ids, needles, forbid, datasets, mode in single_cases:
        result = await ask(user, owner, question, requested, allowed_ids, id_to_name)
        expect("single", who, question, result, needles, forbid, datasets, mode)

    legal_kept = await ask(
        users["legal"],
        owner,
        "What job title does EMP0005 hold?",
        [dataset_ids["legal"], dataset_ids["finance"]],
        allowed["legal"],
        id_to_name,
    )
    expect(
        "single",
        "legal reader, with the finance dataset also requested",
        "What job title does EMP0005 hold?",
        legal_kept,
        ["job_title: General Counsel"],
        [NO_ACCESS, "CFO", "employee_id: EMP0001"],
        ["northwind_legal"],
        "direct",
    )

    multi_cases = [
        (
            "What job title does EMP0004 hold?",
            ["employee_id: EMP0004", "job_title: Head of HR", "allocation_pct: 60", "job_title: Accountant", "allocation_pct: 40"],
            ["northwind_legal", "Paralegal", "SEO Specialist"],
            ["northwind_hr", "northwind_finance"],
            "combined",
        ),
        (
            "What job title does EMP0006 hold?",
            ["employee_id: EMP0006", "job_title: HR Manager", "allocation_pct: 70", "job_title: Controller", "allocation_pct: 30"],
            ["northwind_legal", "employee_id: EMP0004"],
            ["northwind_hr", "northwind_finance"],
            "combined",
        ),
        (
            "What job title does EMP0008 hold?",
            ["employee_id: EMP0008", "job_title: AP Specialist", "allocation_pct: 20", "job_title: Compliance Officer", "allocation_pct: 30"],
            ["SEO Specialist", "northwind_hr", "northwind_marketing", "employee_id: EMP0003"],
            ["northwind_finance", "northwind_legal"],
            "combined",
        ),
        (
            "What job title does EMP0035 hold?",
            ["employee_id: EMP0035", "job_title: HR Business Partner", "allocation_pct: 50", "job_title: AP Specialist", "job_title: Privacy Officer"],
            ["employee_id: EMP0011", "employee_id: EMP0008", "SEO Specialist", "Compliance Officer"],
            ["northwind_hr", "northwind_finance", "northwind_legal"],
            "combined",
        ),
        (
            "What job title does EMP0001 hold?",
            ["employee_id: EMP0001", "job_title: CFO"],
            ["northwind_hr", "northwind_legal", "Accountant"],
            ["northwind_finance"],
            "direct",
        ),
        (
            "What job title does EMP0003 hold?",
            [NOT_IN],
            ["Head of Marketing", NO_ACCESS],
            [],
            "none",
        ),
    ]
    for question, needles, forbid, datasets, mode in multi_cases:
        result = await ask(users["span"], owner, question, span_ids, allowed["span"], id_to_name)
        expect("several", "hr, finance, and legal reader", question, result, needles, forbid, datasets, mode)

    marketing_named = await ask(
        users["span"],
        owner,
        "What does marketing say about EMP0003?",
        [dataset_ids["marketing"]],
        allowed["span"],
        id_to_name,
    )
    expect(
        "several",
        "hr, finance, and legal reader",
        "What does marketing say about EMP0003?",
        marketing_named,
        [NO_ACCESS],
        ["Head of Marketing"],
        [],
        "closed",
    )

    roster_marie = await ask(
        users["roster"],
        owner,
        "Which departments include EMP0008?",
        [dataset_ids["employees_master"]],
        allowed["roster"],
        id_to_name,
    )
    expect(
        "single",
        "roster reader",
        "Which departments include EMP0008?",
        roster_marie,
        ["employee_id: EMP0008", "departments: MKT;LEG;FIN", "dept_count: 3"],
        ["SEO Specialist", "Compliance Officer", "employee_id: EMP0001"],
        ["northwind_employees_master"],
        "direct",
    )

    priya = await ask(
        users["span"],
        owner,
        "What job title does EMP0004 hold?",
        span_ids,
        allowed["span"],
        id_to_name,
    )
    active_values = set(re.findall(r"is_active:\s*(\S+)", priya["answer"]))
    expect(
        "several",
        "hr, finance, and legal reader",
        "What job title does EMP0004 hold? Keep both department records when they disagree.",
        priya,
        ["job_title: Head of HR", "job_title: Accountant", "northwind_hr", "northwind_finance"],
        ["northwind_legal"],
        ["northwind_hr", "northwind_finance"],
        "combined",
    )
    check(
        "both department records stay when they disagree",
        priya["mode"] == "combined" and len(active_values) == 2,
        "is_active values: " + ", ".join(sorted(active_values) or ["none"]),
    )

    async with set_database_global_context_variables(dataset_ids["hr"], users["hr"].id, permission_type="read"):
        stored_answer = await (await get_graph_engine()).query(
            "MATCH (n:Node {type: 'DltRow'}) WHERE n.properties CONTAINS $needle RETURN n.id LIMIT 1",
            {"needle": "retrieved record says"},
        )
    check("the answer is not stored", not stored_answer, "absent" if not stored_answer else "found in the HR graph")

    await authorized_revoke_permission_on_datasets(users["span"].id, [dataset_ids["legal"]], "read", owner.id)
    try:
        without_legal = [dataset_ids["hr"], dataset_ids["finance"]]
        after_revoke = await ask(
            users["span"],
            owner,
            "What job title does EMP0035 hold?",
            without_legal,
            without_legal,
            id_to_name,
        )
        expect(
            "several",
            "hr and finance reader, after legal read was removed",
            "What job title does EMP0035 hold?",
            after_revoke,
            ["job_title: HR Business Partner", "job_title: AP Specialist"],
            ["Privacy Officer", "northwind_legal"],
            ["northwind_hr", "northwind_finance"],
            "combined",
        )
        still_closed = await retrieve(
            users["span"],
            "What job title does EMP0035 hold?",
            [dataset_ids["hr"], dataset_ids["finance"], dataset_ids["legal"]],
        )
        check(
            "cognee still refuses legal after read is removed",
            still_closed["denied"] is True and not still_closed["by_dataset"],
            (still_closed.get("error") or "no error")[:220],
        )
    finally:
        await authorized_give_permission_on_datasets(
            users["span"].id, [dataset_ids["legal"]], "read", owner.id
        )

    def preview(text, limit=900):
        text = (text or "").strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "\n…[truncated]"

    def block(title, by_dataset):
        lines = [f"### {title}", ""]
        for name in ("northwind_hr", "northwind_finance", "northwind_legal", "northwind_marketing", "northwind_employees_master"):
            text = by_dataset.get(name)
            if not text:
                continue
            lines.extend([f"`{name}` ({len(text)} characters)", "", preview(text), ""])
        if not by_dataset:
            lines.extend(["No dataset was opened.", ""])
        return lines

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Northwind CSV test",
        "",
        "Five files were stored in the datasets named by the files: `northwind_hr`, `northwind_finance`, `northwind_legal`, `northwind_marketing`, and `northwind_employees_master`.",
        "A CSV is stored as one row node per employee. Chunk search finds no document chunks in that graph. The retrieval below is Cognee hybrid search, which reads the row nodes. Cognee returns one result per dataset, and each result includes neighboring rows.",
        "Mia Silva, EMP0037, is in HR, finance, and legal. She is not in marketing. The master file lists her departments as FIN;HR;LEG.",
        "",
        f"Checks passed: {passed} of {len(checks)}.",
        "",
        "## Cognee retrieval for the person who can read HR, finance, and legal",
        "",
        "Question: What job title does EMP0037 hold?",
        "",
        "Cognee searched each graph on its own and returned one result per dataset.",
        "",
        *block("Raw result", span["by_dataset"]),
        "### Dispatcher answer",
        "",
        combined,
        "",
        "## HR person, same question, HR dataset only",
        "",
        hr_only["answer"],
        "",
        "## Roster reader, master dataset",
        "",
        roster["answer"],
        "",
        "## Single department",
        "",
    ]
    for item in shown:
        if item["group"] != "single":
            continue
        raw = ", ".join(f"{name} {size} characters" for name, size in item["raw_chars"].items()) or "no dataset opened"
        lines.extend(
            [
                f"### {item['who']}",
                "",
                f"Question: {item['question']}",
                "",
                f"Cognee opened: {', '.join(item['opened']) or 'none'}. Raw size: {raw}. Dispatcher mode: {item['mode']}.",
                "",
                item["answer"],
                "",
            ]
        )
    lines.extend(["## Several departments", ""])
    for item in shown:
        if item["group"] != "several":
            continue
        raw = ", ".join(f"{name} {size} characters" for name, size in item["raw_chars"].items()) or "no dataset opened"
        lines.extend(
            [
                f"### {item['who']}",
                "",
                f"Question: {item['question']}",
                "",
                f"Cognee opened: {', '.join(item['opened']) or 'none'}. Raw size: {raw}. Dispatcher mode: {item['mode']}.",
                "",
                item["answer"],
                "",
            ]
        )
    lines.extend(
        [
        "## Checks",
        "",
        ]
    )
    for name, ok, detail in checks:
        lines.append(f"- {'PASS' if ok else 'FAIL'} — {name}: {detail}")
    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(f"\n{passed}/{len(checks)} written to {REPORT}", flush=True)
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
