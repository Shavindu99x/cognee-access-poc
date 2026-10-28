# Cognee department access

Cognee is the memory and the storage. Dispatcher is the workflow around it. There are two paths.

**Intake.** The organization and the dataset are named before the file is stored. Cognee builds that department's graph, or adds the file to the graph when that dataset already exists. Other departments stay as they are.

**Question.** Cognee checks who is asking, opens only the datasets that person can read, and returns one result per dataset. Dispatcher builds the answer from those results. It keeps the records the question asks for, names the dataset each one came from, and does not store the answer.

Tested with Cognee 1.6.4.

```
Intake
  name the organization and the dataset
        → Cognee stores the file in that dataset and builds the graph
        → readers of that dataset can open it

Question
  the person asks
        → Cognee searches each open dataset and returns one result each
        → Dispatcher keeps the records the question needs and writes one answer
```

> **Scope.** This repository is the access-control proof and the question workflow. It is not a general Cognee manual. Cognee does not choose a department from the text, does not hide a single fact inside a dataset, and does not store an edge from one dataset to another.

---

## Who does what

| Who | What they do | Where to start |
|---|---|---|
| **Management** | Names the organization and the dataset before sending the file. The file is already one department. | [Instructions for management](#instructions-for-management) |
| **Dispatcher** | Stores the file in the named dataset, then on a question returns one retrieval or writes one answer from several. | `.cursor/skills/dispatcher/SKILL.md` |
| **Rules** | What must stay true: the dataset is named before ingestion, grants match the access map, a combined answer is not written back. | `.cursor/skills/dispatcher/RULES.md` |
| **Owner** | Stores the file and grants read on the datasets they own. Not a superuser. Questions are not answered as the owner. | `poc_config.py`, `step1_ingest.py` |
| **Reader** | Asks questions. Can read the datasets named for them on the access map. A title does not add a dataset. | The access map |

The Cursor rule `.cursor/rules/dispatcher.mdc` loads every session and points Dispatcher at the skill and the rules. If those two disagree, the rules win.

---

## Instructions for management

Name the department before the file is ingested. That name is the dataset, and it is the graph. The file is one department when you send it. Choosing that department is done before ingestion.

### What you submit

Send one file together with the organization and the dataset.

A later file for the same department of the same organization uses the same dataset name. It is added to that graph.

A new department needs one more line, in the cover note: who may read it. Until that is known, the file is not stored. A line inside the file does not choose the dataset and does not change who can read it.

The same instructions are in [instructions/for_management.md](instructions/for_management.md).

---

## Workflow

### Intake: the file is stored in the right dataset

1. The submission names the organization and the dataset. The file is already one department. A missing dataset stops the ingest. The file is not opened to choose the department.
2. The access map lists who may read that dataset. A new dataset is written on the map, with its readers, before it is stored. Unknown readers stop the ingest.
3. The owner stores the file. Readers do not ingest. The owner is not a superuser.

```python
await cognee.remember(
    [path_to_the_file],
    dataset_name=dataset_name,
    user=admin,
    self_improvement=False,
)
```

4. Cognee builds one graph and one vector store for that dataset. The same name on a later upload adds to that graph. Finance is not changed by an HR upload.
5. The owner grants `read` to the people named on the access map. A person can be named on one dataset or on several. There is no director and no superuser.
6. When the same person appears in more than one department, the link table records the name, the kind, and the id in each dataset. That row is not an edge between the graphs. Facts stay in the graphs.

### Question: Cognee retrieves, Dispatcher builds the answer

1. The question includes the person who is asking. If that person is the owner, stop. The owner is not used to answer.
2. Dispatcher keeps the datasets that person can read. A dataset the question names and the person cannot read is answered `You do not have access.` The open datasets are still searched.
3. Cognee checks that person, then searches each open graph on its own. A closed dataset in the call is refused before any graph is opened. Dispatcher removes it and calls again with the open datasets only.
4. Cognee returns one result per dataset. An employee number is matched exactly on that record. Other rows in the same graph are left out. A row that only mentions the number, such as a manager id, is not that record.
5. Dispatcher keeps the records that state the fact the question asks for. Shared wording from the question, such as "job" or "employee", is not enough to keep a record. Each kept record is labeled with its dataset.
6. One dataset is the answer. Several datasets are written as one answer, still labeled. When two records disagree, both stay.
7. Every open dataset was searched and nothing remains. The answer is `That is not in the information you can access.`
8. The answer lasts for this question. It is not stored. After `read` is removed, the next question omits that dataset and still searches the datasets that remain.

---

## How Cognee enforces the lock

```
ENABLE_BACKEND_ACCESS_CONTROL = true
        │
recall(question, user=HR) ──► 1. Who is asking?
                               2. ACL lookup: which datasets may this user read?
                               3. Open only those graph and vector files
                               4. Return one result per dataset
                               5. Dispatcher builds the answer from those results
```

| Idea | What it means |
|---|---|
| Dataset | The permission boundary. Not the document, and not the individual fact. |
| Permissions | `read`, `write`, `delete`, `share`. The owner has all four. Everyone else is granted `read` only. |
| Separate files | Each dataset has its own graph file and its own vector store. A forbidden graph is never opened. |
| Closed dataset | Naming a dataset the person cannot read raises `PermissionDeniedError` (HTTP 403) for that call. Dispatcher removes that dataset and searches the open ones. The answer for the closed dataset is `You do not have access.` |
| Open datasets with no answer | The search stays inside the datasets that person can read. The answer is `That is not in the information you can access.` |
| Superuser | Bypasses the lock. This process does not create one. |

---

## Limitations

- The department is named before ingestion. This process does not read the file to choose it or to check it.
- A file stored in a dataset is visible in full to everyone who can read that dataset.
- Read access shows every node in that dataset. Cognee does not hide one fact from a reader of the dataset.
- Cognee searches each dataset on its own and returns one result per dataset.
- Cognee does not connect two datasets. The same name is two nodes. The same entity id in both graphs is still two nodes. A link-table row may name them inside one answer when the reader may see every dataset on that row.
- Cognee may return the only chunk in a dataset even when the question does not match it. Dispatcher keeps the sentences the question asks for.
- The owner can read the datasets they stored. Questions are not run as the owner.
- That answer lasts for the question. It is not written into any graph.
- A dataset belongs to one organization. A later file from another organization does not append into it.
- An instruction inside the file does not choose the dataset and does not grant access.

---

## Original proof

The first proof uses two readers and four documents. Kasun Silva is in the people records and on the finance invoices. The two graphs stay separate: 16 of 16 isolation checks passed, and grant then revoke changed only the finance permission.

| User | Can read | Documents |
|---|---|---|
| `hr.user@nordlight.poc` | `hr_confidential` | `hr_leave_policy.txt`, `hr_employee_records.txt` |
| `finance.user@nordlight.poc` | `finance_confidential` | `fin_q3_budget.txt`, `fin_vendor_payments.txt` |
| `data.admin@nordlight.poc` | owns both | ingests and grants |

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then set an OpenAI or Azure OpenAI key, not both
```

### Run

```bash
python step1_ingest.py             # users, two datasets, grants
python step2_prove_isolation.py    # 16 checks, results/isolation_report.md
python step3_grant_revoke.py       # finance read granted, then removed
python step4_inspect_storage.py    # ACL rows and the graph files
```

Step 1 wipes and rebuilds. Run it again to start the original proof over.

| Test | What it shows |
|---|---|
| T1 | The reader receives their own facts |
| T2–T4 | A forbidden question returns no forbidden facts, including in the raw chunks and the model context |
| T5 | A question about Kasun stays inside the reader's own graph |
| T6–T7 | Naming or writing the other dataset raises `PermissionDeniedError` |

### Earlier separation runs

An earlier version of this skill read a mixed report and separated it before Cognee. That is no longer the ingest path. The dataset is now named before ingestion, and Dispatcher uses Cognee's per-dataset results only when answering.

---

## Files

| Path | Purpose |
|---|---|
| `instructions/for_management.md` | The submission instructions on their own |
| `.cursor/skills/dispatcher/SKILL.md` | The procedure Dispatcher runs |
| `.cursor/skills/dispatcher/RULES.md` | What must stay true |
| `.cursor/rules/dispatcher.mdc` | Loads every session and points at the two files above |
| `poc_config.py` | Users, dataset names, canaries, storage paths |
| `step1_ingest.py` … `step4_inspect_storage.py` | The original two-reader proof |
| `results/isolation_report.md` | 16 of 16 isolation checks |
| `results/oct2026_skill_test.md` | The October report run |

Generated when the proof runs: `.cognee_system/`, `.data_storage/`, `state.json`, `results/`.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| `state.json not found` | Run `python step1_ingest.py` first. |
| `PermissionDeniedError ... [share]` while granting | Pass the dataset id as a `UUID`, not a string. |
| Checks fail with nothing retrieved | The embedding key or model in `.env` is wrong. |
| `ModuleNotFoundError: s3fs` | Unset `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, or install `cognee[aws]`. |
| A department reader sees another department | That file was stored in their dataset. The department is named before the next ingest. |
