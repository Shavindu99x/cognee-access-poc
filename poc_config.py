"""
Shared configuration for the Cognee access-control PoC.

Every step script imports this module FIRST, before importing cognee,
because some settings are environment variables that Cognee reads at import time.
"""

import json
import os
import pathlib

# ---------------------------------------------------------------------------
# 1. Environment switches (must be set BEFORE `import cognee`)
# ---------------------------------------------------------------------------
# EBAC = "Enable Backend Access Control". This is the switch that turns on
# Cognee's multi-user mode: every operation runs as a specific user, every
# dataset gets its own graph + vector database, and every read/write is
# checked against the ACL (access control list) table.
# It is ON by default since Cognee 1.0, but we set it explicitly so the PoC
# never silently runs without it.
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "true")

# Turn off session memory (the short-term cache) for this PoC, so every answer
# provably comes from the permanent, permission-checked knowledge graph and
# nothing is served from a cache.
os.environ.setdefault("CACHING", "false")

ROOT = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
STATE_FILE = ROOT / "state.json"

# Keep all Cognee storage INSIDE the project folder so you can inspect it (step 4).
SYSTEM_ROOT = ROOT / ".cognee_system"   # SQLite (users, ACLs) + graph + vector DBs
DATA_ROOT = ROOT / ".data_storage"      # raw copies of ingested files

# ---------------------------------------------------------------------------
# 2. Principals (users)
# ---------------------------------------------------------------------------
PASSWORD = "poc-password-123"   # demo only, never use in production

ADMIN_EMAIL = "data.admin@nordlight.poc"     # owns both datasets, ingests the documents
HR_EMAIL = "hr.user@nordlight.poc"           # may read HR only
FIN_EMAIL = "finance.user@nordlight.poc"     # may read Finance only

# ---------------------------------------------------------------------------
# 3. Datasets (the unit Cognee puts permissions on)
# ---------------------------------------------------------------------------
HR_DATASET = "hr_confidential"
FIN_DATASET = "finance_confidential"

HR_FILES = [DATA_DIR / "hr" / "hr_leave_policy.txt", DATA_DIR / "hr" / "hr_employee_records.txt"]
FIN_FILES = [DATA_DIR / "finance" / "fin_q3_budget.txt", DATA_DIR / "finance" / "fin_vendor_payments.txt"]

# ---------------------------------------------------------------------------
# 4. Canary facts: strings that exist in exactly ONE dataset.
#    If a canary from the forbidden dataset ever shows up in a user's answer or
#    retrieved context, that is a leak and the test FAILS. This makes the
#    proof automatic instead of "trust me, the answer looks right".
# ---------------------------------------------------------------------------
HR_CANARIES = ["HR-POL-2208", "HR-REC-5521", "EMP-5521", "Band G7", "27 days", "PeopleDesk", "Dilini Fernando"]
FIN_CANARIES = ["FIN-BUD-7731", "FIN-PAY-0417", "INV-90417", "4,870,000", "182,400", "Bluewave", "CAPEX-DC-3390", "223,700"]

# ---------------------------------------------------------------------------
# 5. Answer prompt
#    This prompt only controls the WORDING of the answer. It does not decide
#    what the user may see — Cognee already decided that before the LLM is
#    called, by only retrieving from datasets the user has 'read' on.
#    The proof does not rely on the prompt: step 2 also inspects the raw
#    retrieved chunks and context, where no LLM is involved.
# ---------------------------------------------------------------------------
NO_INFO_ANSWER = "I don't have that information."
SYSTEM_PROMPT = (
    "You are a company knowledge assistant. Answer the question using ONLY the "
    "context provided to you. If the context does not contain the answer, reply "
    f"with exactly: \"{NO_INFO_ANSWER}\" and nothing else. Never guess."
)


def configure_cognee():
    """Point Cognee's storage at the project folder. Call after `import cognee`."""
    import cognee

    cognee.config.system_root_directory(str(SYSTEM_ROOT))
    cognee.config.data_root_directory(str(DATA_ROOT))


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_state() -> dict:
    if not STATE_FILE.exists():
        raise SystemExit("state.json not found. Run step1_ingest.py first.")
    return json.loads(STATE_FILE.read_text())
