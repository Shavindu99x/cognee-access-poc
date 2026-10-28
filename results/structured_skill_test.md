# Structured Brightmoor Q3 2026 report

Dispatcher followed `.cursor/skills/dispatcher/SKILL.md` and `.cursor/skills/dispatcher/RULES.md`.
Each section already names one audience. The section was labeled and stored whole.
The mixed source was never passed to `remember()`.
These datasets are separate from the earlier Brightmoor graphs.

Audiences: company_general, board_confidential, finance_confidential, people_confidential, gtm_confidential, engineering_internal, security_confidential, legal_confidential.

Result: 47/48 checks passed.

| Check | Result | Detail |
|---|---|---|
| company section is one audience | PASS | clean |
| board section is one audience | PASS | clean |
| finance section is one audience | PASS | clean |
| people section is one audience | PASS | clean |
| gtm section is one audience | PASS | clean |
| engineering section is one audience | PASS | clean |
| security section is one audience | PASS | clean |
| legal section is one audience | PASS | clean |
| admin is not a superuser | PASS | data.admin@nordlight.poc |
| employee reader is not a superuser | PASS | employee@brightmoor.poc |
| finance reader is not a superuser | PASS | finance.team@brightmoor.poc |
| people reader is not a superuser | PASS | people.team@brightmoor.poc |
| gtm reader is not a superuser | PASS | gtm.lead@brightmoor.poc |
| engineering reader is not a superuser | PASS | engineering.user@brightmoor.poc |
| security reader is not a superuser | PASS | security.team@brightmoor.poc |
| legal reader is not a superuser | PASS | legal.team@brightmoor.poc |
| cto reader is not a superuser | PASS | cto.user@brightmoor.poc |
| board reader is not a superuser | PASS | board.user@brightmoor.poc |
| director reader is not a superuser | PASS | director.user@brightmoor.poc |
| link table stores shared entities and no canaries | PASS | sofia brandt (2 datasets), lukas hoffmann (2 datasets), medrava (2 datasets), kirkwall (2 datasets), brightmoor flow (2 datasets) |
| employee receives only allowed facts | PASS | probe=summer party own_hit=True foreign=none datasets=['company_general'] |
| employee is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| finance receives only allowed facts | FAIL | probe=INV-24417 own_hit=True foreign=['EUR 610,000'] datasets=['company_general', 'finance_confidential'] |
| finance is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| people receives only allowed facts | PASS | probe=CS-3381 own_hit=True foreign=none datasets=['company_general', 'people_confidential'] |
| people is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| gtm receives only allowed facts | PASS | probe=Brandvik own_hit=True foreign=none datasets=['company_general', 'gtm_confidential'] |
| gtm is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| engineering receives only allowed facts | PASS | probe=KESTREL own_hit=True foreign=none datasets=['company_general', 'engineering_internal'] |
| engineering is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| security receives only allowed facts | PASS | probe=SEC-INC-0814 own_hit=True foreign=none datasets=['company_general', 'security_confidential'] |
| security is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| legal receives only allowed facts | PASS | probe=LGL-2231 own_hit=True foreign=none datasets=['company_general', 'legal_confidential'] |
| legal is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| cto receives only allowed facts | PASS | probe=SEC-INC-0814 own_hit=True foreign=none datasets=['company_general', 'engineering_internal', 'security_confidential'] |
| cto is denied board | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| board receives only allowed facts | PASS | probe=LGL-2231 own_hit=True foreign=none datasets=['board_confidential', 'company_general', 'finance_confidential', 'gtm_confidential', 'legal_confidential', 'people_confidential', 'security_confidential'] |
| board is denied engineering | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| director receives only allowed facts | PASS | probe=LGL-2231 own_hit=True foreign=none datasets=['board_confidential', 'company_general', 'engineering_internal', 'finance_confidential', 'gtm_confidential', 'legal_confidential', 'people_confidential', 'security_confidential'] |
| an employee is denied the people dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| the people team is denied the board dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| the finance team is denied the board term sheet | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| the board is denied the engineering dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| an employee can read the company summer party | PASS | datasets=['company_general'] |
| people neighborhood includes Sofia and leaves the other graphs closed | PASS | same_entity: sofia brandt |
| director neighborhood joins every shared entity | PASS | 5 neighborhoods |
| after revoke the legal dataset stays closed for the director | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| after the legal revoke the director can still read the board dataset | PASS | denied=False datasets=['board_confidential'] |

## Neighborhoods for a reader of every dataset

```
same_entity: sofia brandt
kind: person
From company_general:
  sofia brandt -[is_a]-> person
  sofia brandt -[joins]-> brightmoor
  sofia brandt -[joined_at]-> 2026-11-01
From people_confidential:
  sofia brandt -[is_a]-> person
```

```
same_entity: lukas hoffmann
kind: person
From people_confidential:
  lukas hoffmann -[is_a]-> person
  lukas hoffmann -[on_parental_leave_during]-> 2027-12-01/2027-02-28
  deputy ciso -[covers_duties_for]-> lukas hoffmann
From security_confidential:
  security and it -[owned_by]-> lukas hoffmann
  lukas hoffmann -[is_a]-> person
  exposure of credentials in code repositories -[owned_by]-> lukas hoffmann
```

```
same_entity: medrava
kind: organization
From finance_confidential:
  section 3: finance -[reports_overdue_invoices_for]-> medrava health gmbh
  medrava health gmbh -[is_a]-> organization
  medrava health gmbh -[issued]-> inv-24417
  medrava health gmbh -[issued]-> inv-24452
From gtm_confidential:
  medrava health gmbh -[is_a]-> organization
  customer success -[assigned_executive_sponsor_to]-> medrava health gmbh
  three at-risk accounts churn risk -[concerns]-> medrava health gmbh
  executive sponsor meetings with the three at-risk accounts -[concerns]-> medrava health gmbh
```

```
same_entity: kirkwall
kind: organization
From gtm_confidential:
  kirkwall retail group -[is_a]-> organization
  customer success -[assigned_executive_sponsor_to]-> kirkwall retail group
  three at-risk accounts churn risk -[concerns]-> kirkwall retail group
  executive sponsor meetings with the three at-risk accounts -[concerns]-> kirkwall retail group
From legal_confidential:
  kirkwall retail group -[is_a]-> organization
  kirkwall retail group -[submitted]-> lgl-2231
  respond to kirkwall retail group notice -[responds_to]-> kirkwall retail group
```

```
same_entity: brightmoor flow
kind: product
From company_general:
  brightmoor -[shipped]-> brightmoor flow 5.2
  brightmoor flow 5.2 -[is_a]-> work
From engineering_internal:
  brightmoor flow 5.2 -[is_a]-> software
  brightmoor flow 5.2 -[released_at]-> 2026-08-18
  brightmoor flow 5.2 -[met_reliability_context]-> platform uptime
```

The neighborhood is built for this question only. It is not written back with `remember()`.
