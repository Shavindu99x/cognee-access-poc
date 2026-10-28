"""
STEP 1 — Create users, build two isolated knowledge graphs, grant permissions.

What happens here:
  1. Wipe any previous PoC run (clean, repeatable demo).
  2. Create 3 users: a data admin (owner), an HR user, a Finance user.
  3. The ADMIN ingests the 2 HR documents into dataset "hr_confidential"
     and the 2 Finance documents into dataset "finance_confidential".
     `remember()` = add + cognify: chunk -> LLM entity/relation extraction
     -> knowledge graph + embeddings. With access control ON, each dataset
     gets its OWN graph database and OWN vector database.
  4. The admin grants:
        HR user       -> read on hr_confidential
        Finance user  -> read on finance_confidential
     Nobody else gets anything. The users can't write either.
  5. Save user and dataset IDs to state.json for the next steps.

Run:  python step1_ingest.py
"""

import asyncio
from uuid import UUID

import poc_config as cfg  # must be imported before cognee

import cognee
from cognee.modules.engine.operations.setup import setup as engine_setup
from cognee.modules.users.methods import create_user
from cognee.modules.users.permissions.methods import authorized_give_permission_on_datasets


async def main():
    cfg.configure_cognee()

    print("\n[1/5] Resetting previous PoC data ...")
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    await engine_setup()  # recreate the relational tables (users, datasets, acls, ...)

    print("[2/5] Creating users ...")
    # is_superuser stays False for everyone: a superuser bypasses permissions,
    # which would make the proof meaningless.
    admin = await create_user(cfg.ADMIN_EMAIL, cfg.PASSWORD)
    hr_user = await create_user(cfg.HR_EMAIL, cfg.PASSWORD)
    fin_user = await create_user(cfg.FIN_EMAIL, cfg.PASSWORD)
    for u in (admin, hr_user, fin_user):
        print(f"      {u.email:32}  id={u.id}")

    print("[3/5] Admin ingests HR documents -> dataset 'hr_confidential' (LLM extraction, takes a minute) ...")
    hr_result = await cognee.remember(
        [str(p) for p in cfg.HR_FILES],
        dataset_name=cfg.HR_DATASET,
        user=admin,              # the dataset OWNER is whoever ingests it
        self_improvement=False,  # keep the graph deterministic for the demo
    )
    print("      Admin ingests Finance documents -> dataset 'finance_confidential' ...")
    fin_result = await cognee.remember(
        [str(p) for p in cfg.FIN_FILES],
        dataset_name=cfg.FIN_DATASET,
        user=admin,
        self_improvement=False,
    )
    # remember() returns the dataset id as a STRING. Cognee's permission
    # functions compare against UUID objects, so convert it explicitly,
    # otherwise the grant below is (correctly!) refused with a 403.
    hr_dataset_id = UUID(str(hr_result.dataset_id))
    fin_dataset_id = UUID(str(fin_result.dataset_id))
    print(f"      hr_confidential       id={hr_dataset_id}")
    print(f"      finance_confidential  id={fin_dataset_id}")

    print("[4/5] Granting read permissions (written to the ACL table) ...")
    # Signature: (principal_id, dataset_ids, permission_name, owner_id)
    # owner_id is the user DOING the grant; Cognee checks that they hold
    # 'share' on the dataset (the owner has all four permissions automatically).
    await authorized_give_permission_on_datasets(hr_user.id, [hr_dataset_id], "read", admin.id)
    await authorized_give_permission_on_datasets(fin_user.id, [fin_dataset_id], "read", admin.id)
    print(f"      {cfg.HR_EMAIL}  -> read on {cfg.HR_DATASET}")
    print(f"      {cfg.FIN_EMAIL} -> read on {cfg.FIN_DATASET}")

    cfg.save_state(
        {
            "users": {
                "admin": {"email": admin.email, "id": str(admin.id)},
                "hr": {"email": hr_user.email, "id": str(hr_user.id)},
                "finance": {"email": fin_user.email, "id": str(fin_user.id)},
            },
            "datasets": {
                cfg.HR_DATASET: str(hr_dataset_id),
                cfg.FIN_DATASET: str(fin_dataset_id),
            },
        }
    )
    print(f"[5/5] Saved IDs to {cfg.STATE_FILE.name}. Next: python step2_prove_isolation.py\n")


if __name__ == "__main__":
    asyncio.run(main())
