# Keel HR and finance

Two files were stored in the datasets named before ingestion: `keel_hr` and `keel_finance`.
Both files contain EMP-3304 for Ravi Mendis. HR also has band H5 and 19 days of leave. Finance also has expense EXP-1188.

## Cognee retrieval for the person who can read both

Cognee searched each graph on its own and returned one result per dataset.

### Raw result

`keel_hr`

Keel people record for the people department.

Ravi Mendis is employee EMP-3304. Ravi Mendis is on band H5. Ravi Mendis has 19 days of annual leave.

`keel_finance`

Keel payments record for the finance department.

Ravi Mendis is employee EMP-3304. Ravi Mendis submitted expense EXP-1188 for EUR 4,800 charged to cost center CC-42.

## Dispatcher answer

In keel_hr, the retrieved record says: Ravi Mendis is employee EMP-3304. In keel_finance, the retrieved record says: Ravi Mendis is employee EMP-3304. Ravi Mendis submitted expense EXP-1188 for EUR 4,800 charged to cost center CC-42.

## Finance person asks only for the employee number

In keel_finance, the retrieved record says: Ravi Mendis is employee EMP-3304.

## HR person asks for the number while finance is also listed

In keel_hr, the retrieved record says: Ravi Mendis is employee EMP-3304.

## HR person names finance and asks for the employee number

You do not have access. In keel_hr, the retrieved record says: Ravi Mendis is employee EMP-3304.

## HR person asks for the finance dataset

You do not have access.

## HR person asks for the expense inside the people dataset

That is not in the information you can access.

## Finance person asks for the number and the expense

In keel_finance, the retrieved record says: Ravi Mendis is employee EMP-3304. Ravi Mendis submitted expense EXP-1188 for EUR 4,800 charged to cost center CC-42.

## Owner asks the same question

Questions run as a reader. The owner is not used to answer.

## Checks: 17/17

- PASS: hr file is one department and shares EMP-3304 — clean
- PASS: finance file is one department and shares EMP-3304 — clean
- PASS: owner is not a superuser — keel.admin@keel.poc
- PASS: hr reader is not a superuser — hr.user@keel.poc
- PASS: finance reader is not a superuser — finance.user@keel.poc
- PASS: both reader is not a superuser — hr.finance.user@keel.poc
- PASS: the shared entity id is recorded as two nodes — dd76d537-f136-5b7b-8593-c389320b1eb4
- PASS: hr person is denied the finance dataset — You do not have access.
- PASS: hr person does not receive the finance expense from the people file — That is not in the information you can access.
- PASS: one dataset is trimmed to the employee number — In keel_finance, the retrieved record says: Ravi Mendis is employee EMP-3304.
- PASS: a closed dataset does not cancel the open dataset — In keel_hr, the retrieved record says: Ravi Mendis is employee EMP-3304.
- PASS: naming finance denies that dataset and still answers from people — You do not have access. In keel_hr, the retrieved record says: Ravi Mendis is employee EMP-3304.
- PASS: cognee refuses the whole call when a closed dataset is included — PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
- PASS: cognee returns the shared employee number from both datasets — keel_finance, keel_hr
- PASS: dispatcher keeps the shared number and the finance expense — mode=combined
- PASS: finance person receives only the finance sentences the question asks for — In keel_finance, the retrieved record says: Ravi Mendis is employee EMP-3304. Ravi Mendis submitted expense EXP-1188 for EUR 4,800 charged to cost center CC-42.
- PASS: the owner is not used to answer — Questions run as a reader. The owner is not used to answer.
