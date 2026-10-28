# Brightmoor Q3 2026 management report

Dispatcher followed `.cursor/skills/dispatcher/SKILL.md` and `.cursor/skills/dispatcher/RULES.md`.
Cognee did not split the report. The mixed source was never passed to `remember()`.
The cover line Classification: Confidential was not treated as permission to store the whole file in one dataset.

Audiences: company_general, product, finance, sales, people, it_security, legal, strategy.
These are Brightmoor datasets. They were not added to the Nordlight datasets.
A heading did not decide the audience. Hosting cost went to finance. The resignation, the grievance, pay, and parental leave went to people. The AGPL advice and the service-credit claim went to legal. Quillstream stayed in strategy.

Result: 40/40 checks passed.

| Check | Result | Detail |
|---|---|---|
| general file is one audience | PASS | clean |
| product file is one audience | PASS | clean |
| finance file is one audience | PASS | clean |
| sales file is one audience | PASS | clean |
| people file is one audience | PASS | clean |
| it_security file is one audience | PASS | clean |
| legal file is one audience | PASS | clean |
| strategy file is one audience | PASS | clean |
| admin is not a superuser | PASS | data.admin@nordlight.poc |
| general reader is not a superuser | PASS | general.user@brightmoor.poc |
| product reader is not a superuser | PASS | product.user@brightmoor.poc |
| finance reader is not a superuser | PASS | finance.user@brightmoor.poc |
| sales reader is not a superuser | PASS | sales.user@brightmoor.poc |
| people reader is not a superuser | PASS | people.user@brightmoor.poc |
| it_security reader is not a superuser | PASS | security.user@brightmoor.poc |
| legal reader is not a superuser | PASS | legal.user@brightmoor.poc |
| strategy reader is not a superuser | PASS | strategy.user@brightmoor.poc |
| director is not a superuser | PASS | director.user@brightmoor.poc |
| link table stores shared entities and no canaries | PASS | tessaro (3 datasets), medrava (2 datasets), kirkwall (2 datasets), corvane (2 datasets), mareike lorenz (2 datasets), lukas hoffmann (2 datasets) |
| general reader receives only general facts | PASS | own=['travel policy', 'summer party'] foreign=none datasets=['brightmoor_general'] |
| general reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| product reader receives only product facts | PASS | own=['PM-0912', 'KESTREL'] foreign=none datasets=['brightmoor_product'] |
| product reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| finance reader receives only finance facts | PASS | own=['INV-24417', 'EUR 21,650,000', 'EUR 165 million', 'EUR 9,800,000'] foreign=none datasets=['brightmoor_finance'] |
| finance reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| sales reader receives only sales facts | PASS | own=['Brandvik', 'EUR 4,960,000'] foreign=none datasets=['brightmoor_sales'] |
| sales reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| people reader receives only people facts | PASS | own=['CS-3381', 'Imesha Fonseka', 'EUR 185,000', 'band E5'] foreign=none datasets=['brightmoor_people'] |
| people reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| it_security reader receives only it_security facts | PASS | own=['SEC-INC-0814', 'PT-26-01'] foreign=none datasets=['brightmoor_it_security'] |
| it_security reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| legal reader receives only legal facts | PASS | own=['LGL-2231', 'LGL-2207', 'EP-26-118'] foreign=none datasets=['brightmoor_legal'] |
| legal reader is denied the finance dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| strategy reader receives only strategy facts | PASS | own=['Quillstream', 'EUR 22 to 26 million'] foreign=none datasets=['brightmoor_strategy'] |
| strategy reader is denied the legal dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| director can read every Brightmoor audience | PASS | general=yes, product=yes, finance=yes, sales=yes, people=yes, it_security=yes, legal=yes, strategy=yes |
| director neighborhood joins shared entities | PASS | 6 neighborhoods |
| people reader is denied the strategy dataset | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| after revoke the legal dataset stays closed for the director | PASS | PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| after the legal revoke the director can still read strategy | PASS | denied=False datasets=['brightmoor_strategy'] |

## Neighborhoods for a reader of every Brightmoor audience

```
same_entity: tessaro
kind: organization
From brightmoor_finance:
  finance team -[reviews]-> tessaro deal
  tessaro deal -[is_a]-> event
From brightmoor_sales:
  brightmoor software q3 2026 management report -[records]-> tessaro insurance ag three-year contract
  tessaro insurance ag three-year contract -[is_a]-> contract
  tessaro insurance ag three-year contract -[signed_with]-> tessaro insurance ag
  tessaro insurance ag three-year contract -[sold_by]-> brightmoor software
  tessaro insurance ag three-year contract -[closed_at]-> 2026-09-29
From brightmoor_people:
  nuwan bandara -[raised_grievance_about]-> tessaro deal
  tessaro deal -[is_a]-> work
```

```
same_entity: medrava
kind: organization
From brightmoor_finance:
  medrava health gmbh -[is_a]-> organization
  medrava health gmbh -[is_billed_by]-> inv-24417
  medrava health gmbh -[is_billed_by]-> inv-24452
  inv-24417 -[issued_to]-> medrava health gmbh
  inv-24452 -[issued_to]-> medrava health gmbh
From brightmoor_sales:
  brightmoor software q3 2026 management report -[identifies_as_at_risk]-> medrava health gmbh
  medrava health gmbh -[is_a]-> organization
  customer success -[assigned_executive_sponsor_to]-> medrava health gmbh
```

```
same_entity: kirkwall
kind: organization
From brightmoor_sales:
  brightmoor software q3 2026 management report -[identifies_as_at_risk]-> kirkwall retail group
  kirkwall retail group -[is_a]-> organization
  customer success -[assigned_executive_sponsor_to]-> kirkwall retail group
From brightmoor_legal:
  kirkwall retail group -[is_a]-> organization
  kirkwall retail group -[filed_claim]-> lgl-2231
```

```
same_entity: corvane
kind: organization
From brightmoor_finance:
  corvane ventures -[is_a]-> organization
  corvane ventures -[issued]-> brightmoor software series b term sheet
From brightmoor_strategy:
  board of brightmoor software -[asked_to_grant_exclusivity_to]-> corvane ventures
  corvane ventures -[is_a]-> organization
  corvane ventures -[seeks_exclusivity_for]-> series b
```

```
same_entity: mareike lorenz
kind: person
From brightmoor_people:
  mareike lorenz -[is_a]-> person
  mareike lorenz -[serves_as_ceo_of]-> brightmoor software
  mareike lorenz -[plans_to_step_down_at]-> 2027
From brightmoor_strategy:
  mareike lorenz -[is_a]-> person
  mareike lorenz -[briefed]-> executive team of brightmoor software
  mareike lorenz -[requested_confidentiality_about]-> quillstream analytics ltd
```

```
same_entity: lukas hoffmann
kind: person
From brightmoor_people:
  lukas hoffmann -[is_a]-> person
  lukas hoffmann -[takes_parental_leave_during]-> 2027-12-01/2027-02-28
  deputy ciso -[covers_duties_for]-> lukas hoffmann
From brightmoor_it_security:
  lukas hoffmann -[is_a]-> person
  lukas hoffmann -[presented_findings_of]-> sec-inc-0814
```


The neighborhood is built for this question only. It is not written back with `remember()`.
