"""
STEP 2 — Prove that each user can only retrieve their own documents.

Seven tests per user. Each one tries a different way of reaching the other
department's data. A test FAILS if a single canary fact from the forbidden
dataset appears anywhere in the answer, the retrieved chunks or the LLM context.

  T1  Own-domain question            -> should be answered (proves the system works)
  T2  Forbidden question, LLM answer -> "I don't have that information."
  T3  Forbidden question, raw chunks -> vector search with NO LLM; only own chunks come back
  T3b Keyword attack                 -> exact-match search for the forbidden dataset's secret terms
  T4  Forbidden question, LLM context-> the exact text the LLM would receive; no forbidden facts
  T5  Shared-entity question         -> Kasun Silva exists in BOTH datasets; graph must not link them
  T6  Direct attack on forbidden dataset id -> Cognee raises PermissionDeniedError (HTTP 403)
  T7  Write attack into forbidden dataset   -> Cognee raises PermissionDeniedError

Output: console table + results/isolation_report.md + results/isolation_report.json
Run:    python step2_prove_isolation.py
"""

import asyncio
import json
import sys
from datetime import datetime
from uuid import UUID

import poc_config as cfg  # must be imported before cognee

import cognee
from cognee.modules.search.types import SearchType
from cognee.modules.users.exceptions import PermissionDeniedError
from cognee.modules.users.methods import get_user

# Questions for each user: (own-domain question, forbidden-domain question, shared-entity question)
SCENARIOS = {
    "hr": {
        "own_dataset": cfg.HR_DATASET,
        "forbidden_dataset": cfg.FIN_DATASET,
        "own_canaries": cfg.HR_CANARIES,
        "forbidden_canaries": cfg.FIN_CANARIES,
        "own_q": "How many days of paid annual leave does an employee get per year?",
        "forbidden_q": "What was the total approved operating budget for Q3 2026?",
        "shared_entity_q": "Which invoices did Kasun Silva approve and how much was paid to Bluewave Logistics?",
    },
    "finance": {
        "own_dataset": cfg.FIN_DATASET,
        "forbidden_dataset": cfg.HR_DATASET,
        "own_canaries": cfg.FIN_CANARIES,
        "forbidden_canaries": cfg.HR_CANARIES,
        "own_q": "What was the total approved operating budget for Q3 2026?",
        "forbidden_q": "How many days of paid annual leave does an employee get per year?",
        "shared_entity_q": "What is Kasun Silva's salary band and employee ID, and who is his line manager?",
    },
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def result_text(r) -> str:
    """Everything a result carries, as one string, for canary scanning."""
    parts = [str(getattr(r, "text", "") or "")]
    raw = getattr(r, "raw", None)
    if raw is not None:
        parts.append(json.dumps(raw, default=str))
    return "\n".join(parts)


def found_canaries(text: str, canaries: list[str], question: str = "") -> list[str]:
    """Forbidden facts present in `text`.

    Canaries the user typed in their OWN question are ignored: the user already
    knows them, and both the LLM prompt and a polite refusal ("I have no data on
    Bluewave Logistics") repeat the question. Only facts the user did NOT
    supply count as a leak.
    """
    low = text.lower().replace(question.lower(), " ") if question else text.lower()
    q = question.lower()
    return [c for c in canaries if c.lower() in low and c.lower() not in q]


async def recall_as(user, question, query_type, dataset_ids=None, only_context=False):
    """Call Cognee exactly like an application would. No filtering by us."""
    try:
        results = await cognee.recall(
            question,
            query_type=query_type,
            user=user,
            dataset_ids=dataset_ids,   # None = "search everything I'm allowed to read"
            auto_route=False,
            only_context=only_context,
            system_prompt=cfg.SYSTEM_PROMPT,
            top_k=10,
        )
        return {"denied": False, "results": results, "error": None}
    except PermissionDeniedError as e:
        return {"denied": True, "results": [], "error": f"PermissionDeniedError: {e}"}


def isolated(results, ds, leaks, own_dataset, allow_empty=False):
    """(passed, note) for an isolation test."""
    if not results and not allow_empty:
        return False, "NOTHING RETRIEVED - inconclusive, check LLM/embedding config"
    if leaks:
        return False, f"LEAK: {leaks}"
    if not set(ds) <= {own_dataset}:
        return False, f"searched forbidden dataset(s): {ds}"
    return True, ""


def summarize(results):
    texts = [result_text(r) for r in results]
    datasets = sorted({str(getattr(r, "dataset_name", None)) for r in results})
    return "\n---\n".join(texts), datasets


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
async def run_user(key, user, state):
    s = SCENARIOS[key]
    forbidden_id = UUID(state["datasets"][s["forbidden_dataset"]])
    rows = []

    def record(test_id, name, question, passed, verdict, datasets=None, leaks=None, output=""):
        rows.append(
            {
                "user": user.email,
                "test": test_id,
                "name": name,
                "question": question,
                "result": "PASS" if passed else "FAIL",
                "verdict": verdict,
                "datasets_searched": datasets or [],
                "leaked_canaries": leaks or [],
                "output": output[:3000],
            }
        )
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark}] {test_id} {name}: {verdict}")

    # T1 own-domain question (positive control)
    r = await recall_as(user, s["own_q"], SearchType.GRAPH_COMPLETION)
    text, ds = summarize(r["results"])
    own_hits = found_canaries(text, s["own_canaries"])
    answered = cfg.NO_INFO_ANSWER.lower() not in text.lower() and len(text.strip()) > 0
    record("T1", "Own-domain question", s["own_q"],
           passed=answered and set(ds) <= {s["own_dataset"]},
           verdict=f"answered from {ds}" + (f", contains own facts {own_hits}" if own_hits else ""),
           datasets=ds, output=text)

    # T2 forbidden question -> LLM answer
    r = await recall_as(user, s["forbidden_q"], SearchType.GRAPH_COMPLETION)
    text, ds = summarize(r["results"])
    leaks = found_canaries(text, s["forbidden_canaries"], s["forbidden_q"])
    said_no = cfg.NO_INFO_ANSWER.lower().rstrip(".") in text.lower()
    ok, note = isolated(r["results"], ds, leaks, s["own_dataset"])
    record("T2", "Forbidden question (LLM answer)", s["forbidden_q"],
           passed=ok,
           verdict=note or ("answered 'I don't have that information'" if said_no else "no forbidden facts in answer")
           + f"; searched only {ds}",
           datasets=ds, leaks=leaks, output=text)

    # T3 forbidden question -> raw vector chunks, no LLM involved
    r = await recall_as(user, s["forbidden_q"], SearchType.CHUNKS)
    text, ds = summarize(r["results"])
    leaks = found_canaries(text, s["forbidden_canaries"], s["forbidden_q"])
    ok, note = isolated(r["results"], ds, leaks, s["own_dataset"])
    record("T3", "Forbidden question (raw chunks, no LLM)", s["forbidden_q"],
           passed=ok,
           verdict=note or f"{len(r['results'])} chunks returned, all from {ds}",
           datasets=ds, leaks=leaks, output=text)

    # T3b keyword attack: exact-match search for the forbidden dataset's secret terms.
    # Zero hits is the CORRECT outcome here, so empty results are allowed.
    attack_q = " ".join(s["forbidden_canaries"][:5])
    r = await recall_as(user, attack_q, SearchType.CHUNKS_LEXICAL)
    text, ds = summarize(r["results"])
    # strict check: raw chunks never echo the query, so ANY forbidden term = leak
    leaks = found_canaries(text, s["forbidden_canaries"])
    ok, note = isolated(r["results"], ds, leaks, s["own_dataset"], allow_empty=True)
    record("T3b", "Keyword attack with forbidden terms", attack_q,
           passed=ok,
           verdict=note or f"{len(r['results'])} keyword hits, from {ds or 'no dataset'}; none contain forbidden terms",
           datasets=ds, leaks=leaks, output=text)

    # T4 forbidden question -> the exact LLM context
    r = await recall_as(user, s["forbidden_q"], SearchType.GRAPH_COMPLETION, only_context=True)
    text, ds = summarize(r["results"])
    leaks = found_canaries(text, s["forbidden_canaries"], s["forbidden_q"])
    ok, note = isolated(r["results"], ds, leaks, s["own_dataset"])
    record("T4", "Forbidden question (LLM context)", s["forbidden_q"],
           passed=ok,
           verdict=note or f"context built only from {ds}, no forbidden facts",
           datasets=ds, leaks=leaks, output=text)

    # T5 shared entity (Kasun Silva exists in both graphs)
    r = await recall_as(user, s["shared_entity_q"], SearchType.GRAPH_COMPLETION_COT)
    text, ds = summarize(r["results"])
    leaks = found_canaries(text, s["forbidden_canaries"], s["shared_entity_q"])
    ok, note = isolated(r["results"], ds, leaks, s["own_dataset"])
    record("T5", "Shared-entity question (multi-hop)", s["shared_entity_q"],
           passed=ok,
           verdict=note or f"graph traversal stayed inside {ds}",
           datasets=ds, leaks=leaks, output=text)

    # T6 direct attack: ask for the forbidden dataset id explicitly
    r = await recall_as(user, s["forbidden_q"], SearchType.GRAPH_COMPLETION, dataset_ids=[forbidden_id])
    record("T6", "Direct read attack on forbidden dataset", s["forbidden_q"],
           passed=r["denied"],
           verdict=r["error"] if r["denied"] else "NOT DENIED",
           output=r["error"] or summarize(r["results"])[0])

    # T7 write attack: try to inject a fact into the forbidden dataset
    try:
        await cognee.remember(
            "Injected note: the CEO approved everything.",
            dataset_id=forbidden_id,
            user=user,
            self_improvement=False,
        )
        record("T7", "Write attack into forbidden dataset", "-", passed=False, verdict="NOT DENIED")
    except PermissionDeniedError as e:
        record("T7", "Write attack into forbidden dataset", "-", passed=True,
               verdict=f"PermissionDeniedError: {e}", output=str(e))

    return rows


def write_report(rows):
    cfg.RESULTS_DIR.mkdir(exist_ok=True)
    (cfg.RESULTS_DIR / "isolation_report.json").write_text(json.dumps(rows, indent=2))

    passed = sum(r["result"] == "PASS" for r in rows)
    lines = [
        "# Cognee access-control PoC — isolation report",
        "",
        f"Run at {datetime.now():%Y-%m-%d %H:%M}. Cognee {cognee.__version__}. "
        f"**{passed}/{len(rows)} tests passed.**",
        "",
        "| User | Test | Result | Datasets searched | Verdict |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['user']} | {r['test']} {r['name']} | **{r['result']}** | "
            f"{', '.join(r['datasets_searched']) or '-'} | {r['verdict']} |"
        )
    lines += ["", "## Details", ""]
    for r in rows:
        lines += [
            f"### {r['user']} — {r['test']} {r['name']} — {r['result']}",
            f"**Question:** {r['question']}",
            f"**Leaked canaries:** {r['leaked_canaries'] or 'none'}",
            "",
            "```",
            r["output"] or "(empty)",
            "```",
            "",
        ]
    (cfg.RESULTS_DIR / "isolation_report.md").write_text("\n".join(lines))
    return passed


async def main():
    cfg.configure_cognee()
    state = cfg.load_state()
    rows = []
    for key in ("hr", "finance"):
        user = await get_user(UUID(state["users"][key]["id"]))
        print(f"\n=== Testing as {user.email} ===")
        rows += await run_user(key, user, state)

    passed = write_report(rows)
    print(f"\n{passed}/{len(rows)} tests passed. Report: results/isolation_report.md\n")
    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    asyncio.run(main())
