# Harbor department test

Three files were stored in the datasets named before ingestion: harbor_hr, harbor_finance, and harbor_legal.
Cognee returned one retrieval per dataset. One dataset was returned as retrieved. Several datasets were written into one answer.

## HR answer, returned directly

Harbor people record for the people department.

Leena Voss is employee EMP-7781 on band H3. Leena Voss started on 12 February 2024. Leena Voss has 22 days of annual leave. The staff party code is PARTY-24.

## Director answer about Leena Voss

In harbor_hr, the retrieved record says: Leena Voss is employee EMP-7781 on band H3. Leena Voss started on 12 February 2024. Leena Voss has 22 days of annual leave. In harbor_finance, the retrieved record says: Leena Voss submitted expense EXP-4419 for EUR 3,250 charged to cost center CC-17. Leena Voss's start date on the payment file is 1 March 2024. In harbor_legal, the retrieved record says: Leena Voss is the subject of matter MAT-2204. Clause 9.4 keeps the Leena Voss matter confidential until 30 November 2026.

## Audit fee, returned directly

Harbor payments record for the finance department.

Leena Voss submitted expense EXP-4419 for EUR 3,250 charged to cost center CC-17. Leena Voss's start date on the payment file is 1 March 2024. The Harbor audit fee AUD-19 is EUR 18,000.

## After legal read was removed

In harbor_hr, the retrieved record says: Leena Voss is employee EMP-7781 on band H3. Leena Voss started on 12 February 2024. Leena Voss has 22 days of annual leave. In harbor_finance, the retrieved record says: Leena Voss submitted expense EXP-4419 for EUR 3,250 charged to cost center CC-17. Leena Voss's start date on the payment file is 1 March 2024.

## Checks: 16/16

- PASS: hr file holds only its own canaries — clean
- PASS: finance file holds only its own canaries — clean
- PASS: legal file holds only its own canaries — clean
- PASS: dataset named before ingestion — harbor_access_map.txt
- PASS: owner is not a superuser — harbor.admin@harbor.poc
- PASS: hr reader is not a superuser — hr.user@harbor.poc
- PASS: finance reader is not a superuser — finance.user@harbor.poc
- PASS: legal reader is not a superuser — legal.user@harbor.poc
- PASS: director reader is not a superuser — director.user@harbor.poc
- PASS: existing datasets reused — harbor_finance, harbor_hr, harbor_legal
- PASS: hr answer is the single retrieval — mode=direct
- PASS: finance is denied the legal dataset — PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
- PASS: director retrieval comes back separately from each department — harbor_finance, harbor_hr, harbor_legal
- PASS: combined answer keeps both start dates and names their datasets — mode=combined
- PASS: a question found in one dataset is returned directly — mode=direct used=['harbor_finance'] cognee=['harbor_hr', 'harbor_finance', 'harbor_legal']
- PASS: after revoke the combined answer leaves legal out — mode=combined datasets=['harbor_hr', 'harbor_finance']
