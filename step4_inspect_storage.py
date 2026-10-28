"""
STEP 4 — Look under the hood: where does the isolation physically live?

Prints two pieces of evidence for your PoC presentation:
  1. The ACL table (who may do what on which dataset), read straight from
     Cognee's relational database.
  2. The folder layout: with access control ON, every dataset has its OWN
     graph database and OWN vector database files. The HR graph and the
     Finance graph are different files on disk, which is why "Kasun Silva"
     exists as two unconnected nodes and graph traversal cannot cross over.

Run:  python step4_inspect_storage.py
"""

import asyncio

import poc_config as cfg  # must be imported before cognee

from sqlalchemy import text

from cognee.infrastructure.databases.relational import get_relational_engine

ACL_SQL = """
SELECT u.email AS principal, d.name AS dataset, p.name AS permission
FROM acls a
JOIN permissions p ON p.id = a.permission_id
JOIN datasets d    ON d.id = a.dataset_id
LEFT JOIN users u  ON u.id = a.principal_id
ORDER BY d.name, u.email, p.name
"""


async def main():
    cfg.configure_cognee()
    state = cfg.load_state()
    names = {v["id"]: f"user {v['email']}" for v in state["users"].values()}
    names.update({v: f"dataset {k}" for k, v in state["datasets"].items()})

    print("\n=== 1. ACL table (Cognee's permission source of truth) ===")
    engine = get_relational_engine()
    async with engine.get_async_session() as session:
        rows = (await session.execute(text(ACL_SQL))).all()
    print(f"{'principal':34} {'dataset':24} permission")
    for principal, dataset, permission in rows:
        print(f"{str(principal):34} {dataset:24} {permission}")

    print("\n=== 2. Physical storage layout (.cognee_system/databases) ===")
    db_root = cfg.SYSTEM_ROOT / "databases"
    for path in sorted(db_root.rglob("*")):
        rel = path.relative_to(db_root)
        if len(rel.parts) > 2:
            continue  # skip deep internals of each DB
        label = "  ".join(names.get(part.split(".")[0], "") for part in rel.parts).strip()
        indent = "    " * (len(rel.parts) - 1)
        print(f"{indent}{rel.parts[-1]}{'/' if path.is_dir() else ''}   {('<- ' + label) if label else ''}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
