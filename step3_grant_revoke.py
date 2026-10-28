"""
STEP 3 — Control experiment: grant, then revoke.

A sceptic could say: "Maybe the HR user got 'I don't have that information'
because the LLM was just bad at finding the budget." This step removes that
doubt. We ask the SAME question three times, changing ONLY the ACL:

  A. before grant  -> HR user cannot see the budget
  B. admin grants HR user 'read' on finance_confidential -> now answered (EUR 4,870,000)
  C. admin revokes it again -> HR user cannot see the budget anymore

The only variable that changes is one row in Cognee's ACL table, so the
access decision is provably Cognee's.

Run:  python step3_grant_revoke.py
"""

import asyncio
from uuid import UUID

import poc_config as cfg  # must be imported before cognee

import cognee
from cognee.modules.search.types import SearchType
from cognee.modules.users.methods import get_user
from cognee.modules.users.permissions.methods import (
    authorized_give_permission_on_datasets,
    authorized_revoke_permission_on_datasets,
)

QUESTION = "What was the total approved operating budget for Q3 2026?"


async def ask(user, label):
    results = await cognee.recall(
        QUESTION,
        query_type=SearchType.GRAPH_COMPLETION,
        user=user,
        auto_route=False,
        system_prompt=cfg.SYSTEM_PROMPT,
    )
    text = " ".join(str(getattr(r, "text", "")) for r in results)
    datasets = sorted({str(getattr(r, "dataset_name", None)) for r in results})
    leaked = [c for c in cfg.FIN_CANARIES if c.lower() in text.lower()]
    print(f"\n[{label}] searched {datasets}")
    print(f"   answer: {text.strip()[:300]}")
    print(f"   finance facts visible: {leaked or 'none'}")
    return datasets, leaked, text


async def main():
    cfg.configure_cognee()
    state = cfg.load_state()
    admin = await get_user(UUID(state["users"]["admin"]["id"]))
    hr_user = await get_user(UUID(state["users"]["hr"]["id"]))
    fin_id = UUID(state["datasets"][cfg.FIN_DATASET])

    print(f"Question asked by {hr_user.email}: {QUESTION}")

    ds_a, leak_a, _ = await ask(hr_user, "A. before grant")

    await authorized_give_permission_on_datasets(hr_user.id, [fin_id], "read", admin.id)
    print(f"\n>>> admin GRANTS read on {cfg.FIN_DATASET} to {hr_user.email}")
    ds_b, leak_b, _ = await ask(hr_user, "B. after grant")

    await authorized_revoke_permission_on_datasets(hr_user.id, [fin_id], "read", admin.id)
    print(f"\n>>> admin REVOKES read on {cfg.FIN_DATASET} from {hr_user.email}")
    ds_c, leak_c, _ = await ask(hr_user, "C. after revoke")

    ok = (not leak_a) and (cfg.FIN_DATASET in ds_b) and (not leak_c) and (cfg.FIN_DATASET not in ds_c)
    print("\nRESULT:", "PASS — access follows the ACL exactly." if ok else "CHECK OUTPUT ABOVE")
    print("(In B the answer should contain the finance budget. If B has the dataset but no")
    print(" figure, the LLM phrased it differently; the 'searched' list is the hard evidence.)\n")


if __name__ == "__main__":
    asyncio.run(main())
