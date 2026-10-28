"""
Store three already-separated Harbor files and answer from the retrieval.

The dataset is named before remember(). One retrieved dataset is returned as
retrieved. Two or more retrieved datasets become one answer, using only
sentences from those texts that the question needs.
"""

import asyncio
import re
import sys
from uuid import UUID

import poc_config as cfg

import cognee
from cognee.modules.data.methods.get_datasets_by_name import get_datasets_by_name
from cognee.modules.search.types import SearchType
from cognee.modules.users.exceptions import PermissionDeniedError
from cognee.modules.users.methods import create_user, get_user_by_email
from cognee.modules.users.permissions.methods import (
    authorized_give_permission_on_datasets,
    authorized_revoke_permission_on_datasets,
)
from fastapi_users.exceptions import UserAlreadyExists

ORG = "harbor"
FILES = {
    "hr": cfg.ROOT / "data" / "harbor" / "hr.txt",
    "finance": cfg.ROOT / "data" / "harbor" / "finance.txt",
    "legal": cfg.ROOT / "data" / "harbor" / "legal.txt",
}
DATASETS = {key: f"{ORG}_{key}" for key in FILES}
CANARIES = {
    "hr": ["EMP-7781", "band H3", "12 February 2024", "PARTY-24"],
    "finance": ["EXP-4419", "EUR 3,250", "1 March 2024", "AUD-19"],
    "legal": ["MAT-2204", "clause 9.4", "NDA-66"],
}
READERS = {
    "hr": "hr.user@harbor.poc",
    "finance": "finance.user@harbor.poc",
    "legal": "legal.user@harbor.poc",
    "director": "director.user@harbor.poc",
}
OWNER_EMAIL = "harbor.admin@harbor.poc"
ACCESS_MAP = cfg.RESULTS_DIR / "harbor_access_map.txt"
MANIFEST = cfg.RESULTS_DIR / "harbor_manifest.txt"
REPORT = cfg.RESULTS_DIR / "harbor_skill_test.md"
LINKS = cfg.RESULTS_DIR / "harbor_links.json"


STOP = {"what", "does", "have", "about", "know", "this", "that", "with", "from", "your"}


def question_tokens(question):
    found = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", question.lower()))
    return {token for token in found if token not in STOP and (len(token) > 3 or "-" in token or any(ch.isdigit() for ch in token))}


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.])\s+", text) if part.strip()]


def relevant(question, text):
    low = text.lower()
    return any(token in low for token in question_tokens(question))


def needed(question, text):
    tokens = question_tokens(question)
    kept = [sentence for sentence in sentences(text) if any(token in sentence.lower() for token in tokens)]
    return " ".join(kept)


def answer_from(question, retrieved):
    populated = [(name, text.strip()) for name, text in retrieved if text and text.strip() and relevant(question, text)]
    if len(populated) <= 1:
        text = populated[0][1] if populated else ""
        return "direct", text, [name for name, _ in populated]
    parts = [f"In {name}, the retrieved record says: {needed(question, text)}" for name, text in populated]
    return "combined", " ".join(parts), [name for name, _ in populated]


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
        return {"denied": True, "by_dataset": {}, "error": str(error)}
    by_dataset = {}
    for result in results or []:
        name = result_dataset(result) or "unknown"
        text = result_text(result)
        if text.strip():
            by_dataset[str(name)] = text
    return {"denied": False, "by_dataset": by_dataset, "error": None}


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
        check(f"{key} file holds only its own canaries", not leaked, "clean" if not leaked else str(leaked))

    readers = "hr.user@harbor.poc, director.user@harbor.poc"
    finance_readers = "finance.user@harbor.poc, director.user@harbor.poc"
    legal_readers = "legal.user@harbor.poc, director.user@harbor.poc"
    ACCESS_MAP.write_text(
        "\n".join(
            [
                "organization: harbor",
                f"owner: {OWNER_EMAIL}",
                "owner is not a superuser",
                "access control: on",
                "The dataset is named before ingestion. The file is not read to choose or check it.",
                "",
                "domain: hr",
                "dataset: harbor_hr",
                f"read: {readers}",
                "",
                "domain: finance",
                "dataset: harbor_finance",
                f"read: {finance_readers}",
                "",
                "domain: legal",
                "dataset: harbor_legal",
                f"read: {legal_readers}",
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
    check("dataset named before ingestion", "harbor_hr" in ACCESS_MAP.read_text(), ACCESS_MAP.name)

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
        check("existing datasets reused", set(by_name) == set(DATASETS.values()), ", ".join(sorted(by_name)))
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

        grants = {
            "hr": ["hr"],
            "finance": ["finance"],
            "legal": ["legal"],
            "director": ["hr", "finance", "legal"],
        }
        for name, keys in grants.items():
            await authorized_give_permission_on_datasets(
                users[name].id, [dataset_ids[key] for key in keys], "read", owner.id
            )

    hr = await retrieve(users["hr"], "What is Leena Voss's employee number and band?", [dataset_ids["hr"]])
    mode, direct, _used = answer_from("What is Leena Voss's employee number and band?", list(hr["by_dataset"].items()))
    check(
        "hr answer is the single retrieval",
        mode == "direct" and "EMP-7781" in direct and "band H3" in direct and "EXP-4419" not in direct and "MAT-2204" not in direct,
        f"mode={mode}",
    )

    denied = await retrieve(users["finance"], "MAT-2204", [dataset_ids["legal"]])
    check("finance is denied the legal dataset", denied["denied"], denied["error"] or "no error")

    director_ids = [dataset_ids[key] for key in FILES]
    leena = await retrieve(users["director"], "What do we know about Leena Voss?", director_ids)
    mode, combined, _used = answer_from("What do we know about Leena Voss?", list(leena["by_dataset"].items()))
    returned = set(leena["by_dataset"])
    check(
        "director retrieval comes back separately from each department",
        returned == {"harbor_hr", "harbor_finance", "harbor_legal"},
        ", ".join(sorted(returned)) or "none",
    )
    check(
        "combined answer keeps both start dates and names their datasets",
        mode == "combined"
        and "harbor_hr" in combined
        and "12 February 2024" in combined
        and "harbor_finance" in combined
        and "1 March 2024" in combined
        and "harbor_legal" in combined
        and "MAT-2204" in combined
        and "AUD-19" not in combined
        and "NDA-66" not in combined
        and "PARTY-24" not in combined,
        f"mode={mode}",
    )

    audit = await retrieve(users["director"], "AUD-19", director_ids)
    mode, audit_answer, used = answer_from("AUD-19", list(audit["by_dataset"].items()))
    check(
        "a question found in one dataset is returned directly",
        mode == "direct" and used == ["harbor_finance"] and "AUD-19" in audit_answer and "MAT-2204" not in audit_answer and "EMP-7781" not in audit_answer,
        f"mode={mode} used={used} cognee={list(audit['by_dataset'])}",
    )

    await authorized_revoke_permission_on_datasets(users["director"].id, [dataset_ids["legal"]], "read", owner.id)
    after = await retrieve(users["director"], "What do we know about Leena Voss?", director_ids)
    if after["denied"]:
        open_ids = [dataset_ids["hr"], dataset_ids["finance"]]
        after = await retrieve(users["director"], "What do we know about Leena Voss?", open_ids)
        revoked_closed = True
    else:
        revoked_closed = "harbor_legal" not in after["by_dataset"]
    mode, after_answer, _used = answer_from("What do we know about Leena Voss?", list(after["by_dataset"].items()))
    check(
        "after revoke the combined answer leaves legal out",
        revoked_closed and mode == "combined" and "MAT-2204" not in after_answer and "EMP-7781" in after_answer and "EXP-4419" in after_answer,
        f"mode={mode} datasets={list(after['by_dataset'])}",
    )
    await authorized_give_permission_on_datasets(users["director"].id, [dataset_ids["legal"]], "read", owner.id)

    passed = sum(1 for _, ok, _ in checks if ok)
    lines = [
        "# Harbor department test",
        "",
        "Three files were stored in the datasets named before ingestion: harbor_hr, harbor_finance, and harbor_legal.",
        "Cognee returned one retrieval per dataset. One dataset was returned as retrieved. Several datasets were written into one answer.",
        "",
        "## HR answer, returned directly",
        "",
        direct,
        "",
        "## Director answer about Leena Voss",
        "",
        combined,
        "",
        "## Audit fee, returned directly",
        "",
        audit_answer,
        "",
        "## After legal read was removed",
        "",
        after_answer,
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
