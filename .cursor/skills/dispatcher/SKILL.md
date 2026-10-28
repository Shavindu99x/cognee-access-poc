---
name: dispatcher
description: >-
  Dispatcher stores a file in the dataset named before ingestion, grants read
  per dataset, and answers as the person who asked. A closed dataset is
  answered "You do not have access." One retrieved dataset is returned as
  retrieved. When several datasets that person can read contain what the
  question needs, Dispatcher writes one answer from those texts. Use when
  ingesting a file into a named Cognee dataset, granting or revoking dataset
  access, recalling memory, or answering a question that may span datasets.
---

# Dispatcher

Procedure for the rules in [RULES.md](RULES.md). Read that file first. Cognee is the only memory store.

A domain is one audience with the same read permission, stored as one dataset and one graph. The dataset is named before ingestion. Dataset names have no spaces or dots. A department list from one company is not the list for the next company.

## Checklist

```
- [ ] The submission already names the organization and the dataset
- [ ] RULES.md Sync Set A — access map, dataset, grants, when the dataset is new
- [ ] RULES.md gate passed — named dataset, readers known, no foreign organization in the target dataset
- [ ] RULES.md Sync Set B — manifest, remember() into that dataset, link table
- [ ] RULES.md Sync Set C — ACL matches the access map
- [ ] RULES.md Sync Set D — owner refused, closed dataset removed, sentences limited to the question
- [ ] RULES.md §5 — hard stops clear
```

## 1. Access map (Sync Set A)

Write this before `remember()` when the dataset is new. An existing dataset for this organization already has this row.

- **Owner**: calls `remember()` and holds `share`. Not a superuser.
- **Domain**: one audience, one dataset name.
- **Principal**: who calls `recall()`, and the datasets they may read.

A dataset with no known readers stops the run. Ask who may read it. Readers and dataset names belong to one organization. Do not reuse another organization's principals or datasets.

`ENABLE_BACKEND_ACCESS_CONTROL` is true for the whole process.

## 2. Store the named dataset (Sync Set B)

The department and the dataset are named before this step. Do not read the file to choose them. Do not read the file to check them.

1. Read the organization and the dataset from the submission. A missing dataset stops the run.
2. Use the dataset on this organization's access map when that name is already there. `remember()` then adds the file to that graph.
3. A dataset missing from the access map is new. Complete Sync Set A before ingest. If who may read it is unknown, stop. Do not store the file in a dataset that already exists.
4. Give the dataset a name with no spaces or dots. If this Cognee instance holds more than one organization, or the bare audience name is already in use, name it `{organization}_{audience}` using the slug on the access map.
5. Run the gate in RULES.md, "Gate, before `remember()`." Any failure stops the ingest.
6. Write the manifest row. Ingest this file into this dataset only.

Manifest row:

```text
source: <original file or note>
dataset: <dataset_name>
canaries: <strings that exist in this file>
```

Canaries are how a later recall proves isolation.

## 3. Store (Sync Set B)

Import project config before `import cognee` when this repo's `poc_config.py` is in use, then `configure_cognee()`.

Call `remember()` only after the gate has passed. One call, as the owner, for the named dataset:

```python
await cognee.remember(
    [path_to_the_file],
    dataset_name=dataset_name,
    user=owner,
    self_improvement=False,
)
```

The same `dataset_name` on a later call adds to that graph. End principals do not ingest.

Cognee builds one graph and one vector store per dataset and checks the ACL on every later read.

## 4. Grant (Sync Set C)

Grant `read` only. The owner already has `read`, `write`, `delete`, and `share`.

```python
await authorized_give_permission_on_datasets(
    principal_id, [dataset_id], "read", owner_id
)
```

`dataset_id` is a `UUID`. A string id fails the grant.

Revoke removes that permission. The next recall uses the new ACL.

## 5. Link table (Sync Set B)

Build this as the owner after the graphs exist. Replace the table. Do not keep ids from a graph that was rebuilt.

One row is one real-world entity that appears in two or more datasets.

```text
name: <entity name>
kind: person | organization | product
datasets:
  <dataset_name>: <entity id>
  <dataset_name>: <entity id>
```

The row stores the name, the kind, and the ids. Facts stay in the dataset graphs. An equal entity id in two datasets is not an edge. The graphs stay separate.

## 6. Answer (Sync Set D)

Recall as the asking principal. Search only datasets that principal can read. A granted principal who does not own the dataset is queried with `dataset_ids`. The dataset name resolves only for the owner.

```python
await cognee.search(
    query_text=question,
    query_type=SearchType.CHUNKS_LEXICAL,
    dataset_ids=readable_dataset_ids,
    user=principal,
    only_context=True,
)
```

Cognee returns one result per dataset. Keep each result with its dataset name. Drop a dataset that returned no text.

The question runs as the person who asked. If that person is the owner, stop. Do not call `recall()`. Cognee would allow the owner to read the datasets they stored. Dispatcher does not. There is no director and no superuser. Read comes from the access map.

Call `recall()` with the open datasets only. If a call included a closed dataset and raised `PermissionDeniedError`, call again with that dataset removed. Do not put the closed dataset in the second call.

When the question contains an employee number, do not use a similarity search for that number. After Cognee's read check, match `employee_id` to that number in each open dataset. A row that only mentions the number, such as a manager id, is not the record. A question with no employee number still uses the search above.

A dataset or audience the question names, and the person cannot read, is answered `You do not have access.` That refusal does not cancel the open datasets. A question that only names the closed dataset gets that sentence and no substitute from another dataset. A question that does not name a dataset searches the open datasets only, and a miss there is `That is not in the information you can access.`

Cognee may return the only chunk in a dataset even when it does not match the question. Drop that chunk unless a sentence in it states a fact the question asks for. A shared general word is not that fact. An identifier in the question keeps only the sentences that contain that identifier. This trim applies when one dataset answered and when several did.

Write one answer from the remaining sentences. Name the dataset each sentence came from. When two texts disagree, keep both and name the dataset each came from. A link-table row may say the name is the same entity. The same entity id in two datasets is still two nodes. Use the row only when every dataset on it returned a sentence and the person can read every one of them.

The answer lasts for this question. Do not call `remember()` with it.

## 7. Check

- A question asked as the owner does not call `recall()`.
- A named dataset the person cannot read is answered `You do not have access.` and contributes no text. The open datasets are still searched.
- Open datasets that do not answer the question are answered `That is not in the information you can access.`
- The answer, from one dataset or from several, contains only sentences that state a fact the question asks for.
- After `read` is removed, the next question omits that dataset and still searches the datasets that remain.

## Example

This example is not a rule, and these department names are not the product's list. The rules in [RULES.md](RULES.md) hold when the organization, the audiences, and the file are different.

People sends `people_records.txt` and names the dataset `hr_confidential` before ingestion. Payments sends `payments.txt` and names `finance_confidential` before ingestion.

- `remember()` each file into the dataset that submission named.
- HR person: `read` on `hr_confidential`. Finance person: `read` on `finance_confidential`. A third person: `read` on both, because the access map says so.
- Link table: `Kasun Silva`, kind `person`, one entity id in each dataset.
- The HR person asks for the finance dataset. The answer is `You do not have access.` The finance graph stays closed. A people question in the same search is still answered from `hr_confidential`.
- The HR person asks a question the people file does not answer, and does not name finance. The answer is `That is not in the information you can access.`
- The finance person asks only for the employee number. The expense sentence in that same chunk is left out.
- The person with both grants asks about Kasun. Both datasets return text. The answer uses the sentences the question needs. The same entity id in both graphs is not an edge. The answer is not stored.
