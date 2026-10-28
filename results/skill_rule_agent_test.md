# Skill, rules, and agent test

The agent followed `.cursor/skills/cognee-domain-access/SKILL.md` and `RULES.md`.
Cognee did not split the mixed briefing. The agent separated it and labeled each file with one department before `remember()`.

Source not ingested: `data/incoming/q4_management_briefing.txt`
HR file ingested: `data/labeled/hr/q4_people_section.txt`
Finance file ingested: `data/labeled/finance/q4_payments_section.txt`

Result: 11/11 checks passed. The first link lookup missed Kasun because Cognee stores the entity name in lowercase (`kasun silva`). The same graphs were read again with that name. The id is the same in both datasets because Cognee derives it from the name. The nodes still sit in two separate graph files, with no edge between those files.

| Check | Result | Detail |
|---|---|---|
| mixed file was separated before ingest | PASS | labeled files do not contain the mixed-source marker |
| each labeled file is one department | PASS | HR file has only HR canaries; finance file has only finance canaries |
| remember() is not given the mixed file | PASS | calls use q4_people_section.txt and q4_payments_section.txt only |
| director is not a superuser | PASS | director.user@nordlight.poc |
| link table stores ids only | PASS | hr_confidential and finance_confidential both map to entity id 7d93769f-40e8-5c00-a606-73c0d2a87a21. No canaries in the link table. |
| HR principal receives the HR section | PASS | datasets=['hr_confidential'] canaries=['HR-BRIEF-8841', 'LEAD-8841'] |
| HR principal does not receive finance facts | PASS | finance canaries in HR context=none |
| forbidden dataset raises PermissionDeniedError | PASS | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| director receives both sides and a same_entity neighborhood | PASS | hr=['HR-BRIEF-8841', 'LEAD-8841'] finance=['FIN-BRIEF-2290', 'INV-91002'] edges=12 HR + 6 finance |
| neighborhood was not written back into a dataset | PASS | neighborhood exists only in this run |
| after revoke the finance dataset stays closed | PASS | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |

## Director neighborhood for this question

```
same_entity: Kasun Silva
kind: person
From hr_confidential:
  kasun silva -[reports_to]-> dilini fernando
  kasun silva -[completed]-> leadership review lead-8841
  kasun silva -[holds_role]-> senior procurement manager
From finance_confidential:
  kasun silva -[approved]-> inv-91002
  payment 1 — inv-90417 -[approved_by]-> kasun silva
  payment 3 — inv-90468 -[approved_by]-> kasun silva
```
