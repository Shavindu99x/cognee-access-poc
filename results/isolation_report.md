# Cognee access-control PoC — isolation report

Run at 2026-10-17 14:43. Cognee 1.6.4. **16/16 tests passed.**

| User | Test | Result | Datasets searched | Verdict |
|---|---|---|---|---|
| hr.user@nordlight.poc | T1 Own-domain question | **PASS** | hr_confidential | answered from ['hr_confidential'], contains own facts ['27 days'] |
| hr.user@nordlight.poc | T2 Forbidden question (LLM answer) | **PASS** | hr_confidential | answered 'I don't have that information'; searched only ['hr_confidential'] |
| hr.user@nordlight.poc | T3 Forbidden question (raw chunks, no LLM) | **PASS** | hr_confidential | 2 chunks returned, all from ['hr_confidential'] |
| hr.user@nordlight.poc | T3b Keyword attack with forbidden terms | **PASS** | hr_confidential | 2 keyword hits, from ['hr_confidential']; none contain forbidden terms |
| hr.user@nordlight.poc | T4 Forbidden question (LLM context) | **PASS** | hr_confidential | context built only from ['hr_confidential'], no forbidden facts |
| hr.user@nordlight.poc | T5 Shared-entity question (multi-hop) | **PASS** | hr_confidential | graph traversal stayed inside ['hr_confidential'] |
| hr.user@nordlight.poc | T6 Direct read attack on forbidden dataset | **PASS** | - | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| hr.user@nordlight.poc | T7 Write attack into forbidden dataset | **PASS** | - | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [write] for all datasets requested. (Status code: 403) |
| finance.user@nordlight.poc | T1 Own-domain question | **PASS** | finance_confidential | answered from ['finance_confidential'], contains own facts ['4,870,000'] |
| finance.user@nordlight.poc | T2 Forbidden question (LLM answer) | **PASS** | finance_confidential | answered 'I don't have that information'; searched only ['finance_confidential'] |
| finance.user@nordlight.poc | T3 Forbidden question (raw chunks, no LLM) | **PASS** | finance_confidential | 2 chunks returned, all from ['finance_confidential'] |
| finance.user@nordlight.poc | T3b Keyword attack with forbidden terms | **PASS** | finance_confidential | 2 keyword hits, from ['finance_confidential']; none contain forbidden terms |
| finance.user@nordlight.poc | T4 Forbidden question (LLM context) | **PASS** | finance_confidential | context built only from ['finance_confidential'], no forbidden facts |
| finance.user@nordlight.poc | T5 Shared-entity question (multi-hop) | **PASS** | finance_confidential | graph traversal stayed inside ['finance_confidential'] |
| finance.user@nordlight.poc | T6 Direct read attack on forbidden dataset | **PASS** | - | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403) |
| finance.user@nordlight.poc | T7 Write attack into forbidden dataset | **PASS** | - | PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [write] for all datasets requested. (Status code: 403) |

## Details

### hr.user@nordlight.poc — T1 Own-domain question — PASS
**Question:** How many days of paid annual leave does an employee get per year?
**Leaked canaries:** none

```
Every permanent employee receives **27 days of paid annual leave per calendar year**. Employees with more than five years of service receive **3 additional loyalty days**, totaling **30 days**.
{"value": "Every permanent employee receives **27 days of paid annual leave per calendar year**. Employees with more than five years of service receive **3 additional loyalty days**, totaling **30 days**."}
```

### hr.user@nordlight.poc — T2 Forbidden question (LLM answer) — PASS
**Question:** What was the total approved operating budget for Q3 2026?
**Leaked canaries:** none

```
I don't have that information.
{"value": "I don't have that information."}
```

### hr.user@nordlight.poc — T3 Forbidden question (raw chunks, no LLM) — PASS
**Question:** What was the total approved operating budget for Q3 2026?
**Leaked canaries:** none

```
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Employee Records Extract, October 2026
Record set: HR-REC-5521
Classification: HR CONFIDENTIAL

Employee: Kasun Silva
Employee ID: EMP-5521
Role: Senior Procurement Manager
Department: Operations
Start date: 4 February 2019
Salary band: Band G7
Annual leave remaining in 2026: 11 days
Line manager: Dilini Fernando

Employee: Tharushi Perera
Employee ID: EMP-6043
Role: Data Engineer
Department: Technology
Start date: 15 June 2023
Salary band: Band G5
Annual leave remaining in 2026: 19 days
Line manager: Kasun Silva

Notes:
Tharushi Perera completed the "Lakehouse Foundations" internal training in September 2026.
Kasun Silva is scheduled for a performance review on 12 November 2026.

{"id": "513b9992-a810-5b36-bf69-a51f17b9ea7d", "created_at": 1792221101296, "updated_at": 1792221101296, "ontology_valid": false, "ontology_uri": null, "version": 1, "topological_rank": 0, "valid_to": null, "type": "IndexSchema", "belongs_to_set": [], "source_pipeline": null, "source_task": null, "source_node_set": null, "source_user": null, "source_content_hash": null, "feedback_weight": 0.5, "importance_weight": 0.5, "text": "NORDLIGHT SOLUTIONS \u2014 HUMAN RESOURCES\nDocument: Employee Records Extract, October 2026\nRecord set: HR-REC-5521\nClassification: HR CONFIDENTIAL\n\nEmployee: Kasun Silva\nEmployee ID: EMP-5521\nRole: Senior Procurement Manager\nDepartment: Operations\nStart date: 4 February 2019\nSalary band: Band G7\nAnnual leave remaining in 2026: 11 days\nLine manager: Dilini Fernando\n\nEmployee: Tharushi Perera\nEmployee ID: EMP-6043\nRole: Data Engineer\nDepartment: Technology\nStart date: 15 June 2023\nSalary band: Band G5\nAnnual leave remaining in 2026: 19 days\nLine manager: Kasun Silva\n\nNotes:\nTharushi Perera completed the \"Lakehouse Foundations\" internal training in September 2026.\nKasun Silva is scheduled for a performance review on 12 November 2026.\n", "document_id": "8b0ddcf0-7ea9-4403-9b8b-9ba3aa907dce", "document_name": "hr_employee_records", "chunk_index": 0, "source_chunk_id": null, "external_metadata": "{\"_cognee\": {\"source_uri\": \"file:///Users/shavinduk/Documents/Cognee%20POC/cognee-access-poc/data/hr/hr_employee_records.txt\"}}", "score": 0.7074865102767944}
---
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Annual Leave and Remote Work Policy 2026
Policy reference: HR-POL-2208
Classification: HR CONFIDENTIAL

1. Annual leave
Every permanent employee of Nordlight Solutions receives 27 days of paid annual leave per calendar year.
Employees with more than five years of service receive 3 additional loyalty days, for a total of 30 days.
Unused annual leave may be carried over into the next year, up to a maximum of 8 days.
Carried-over days expire on 31 March of the following year.

2. Sick leave
Employees may take up to 14 days of paid sick leave per year.
A medical certificate is required for any sick leave longer than 3 consecutive days.

3. Remote work
Employees may work remot
```

### hr.user@nordlight.poc — T3b Keyword attack with forbidden terms — PASS
**Question:** FIN-BUD-7731 FIN-PAY-0417 INV-90417 4,870,000 182,400
**Leaked canaries:** none

```
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Employee Records Extract, October 2026
Record set: HR-REC-5521
Classification: HR CONFIDENTIAL

Employee: Kasun Silva
Employee ID: EMP-5521
Role: Senior Procurement Manager
Department: Operations
Start date: 4 February 2019
Salary band: Band G7
Annual leave remaining in 2026: 11 days
Line manager: Dilini Fernando

Employee: Tharushi Perera
Employee ID: EMP-6043
Role: Data Engineer
Department: Technology
Start date: 15 June 2023
Salary band: Band G5
Annual leave remaining in 2026: 19 days
Line manager: Kasun Silva

Notes:
Tharushi Perera completed the "Lakehouse Foundations" internal training in September 2026.
Kasun Silva is scheduled for a performance review on 12 November 2026.

{"name": "", "type": "DocumentChunk", "created_at": 1792221085881, "updated_at": 1792221085881, "ontology_valid": false, "ontology_uri": null, "version": 1, "topological_rank": 2, "valid_to": null, "metadata": {"index_fields": ["text"]}, "belongs_to_set": null, "source_pipeline": "cognify_pipeline", "source_task": "extract_chunks_from_documents", "source_node_set": null, "source_user": "data.admin@nordlight.poc", "source_content_hash": "416b60a6ac346fea76981d981f715810", "feedback_weight": 0.5, "importance_weight": 0.5, "text": "NORDLIGHT SOLUTIONS \u2014 HUMAN RESOURCES\nDocument: Employee Records Extract, October 2026\nRecord set: HR-REC-5521\nClassification: HR CONFIDENTIAL\n\nEmployee: Kasun Silva\nEmployee ID: EMP-5521\nRole: Senior Procurement Manager\nDepartment: Operations\nStart date: 4 February 2019\nSalary band: Band G7\nAnnual leave remaining in 2026: 11 days\nLine manager: Dilini Fernando\n\nEmployee: Tharushi Perera\nEmployee ID: EMP-6043\nRole: Data Engineer\nDepartment: Technology\nStart date: 15 June 2023\nSalary band: Band G5\nAnnual leave remaining in 2026: 19 days\nLine manager: Kasun Silva\n\nNotes:\nTharushi Perera completed the \"Lakehouse Foundations\" internal training in September 2026.\nKasun Silva is scheduled for a performance review on 12 November 2026.\n", "chunk_size": 283, "chunk_index": 0, "cut_type": "paragraph_end", "content_hash": "fe068a8190519fd10fe18415f626420ec2f625ce1d9e6931e0f5c7ca4a52f6d1", "max_chunk_tokens": 4096, "chunker_id": "text_chunker_v1", "document_id": "8b0ddcf0-7ea9-4403-9b8b-9ba3aa907dce", "document_name": "hr_employee_records", "external_metadata": "{\"_cognee\": {\"source_uri\": \"file:///Users/shavinduk/Documents/Cognee%20POC/cognee-access-poc/data/hr/hr_employee_records.txt\"}}", "truth_alignment": null, "truth_epoch": null, "id": "513b9992-a810-5b36-bf69-a51f17b9ea7d"}
---
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Annual Leave and Remote Work Policy 2026
Policy reference: HR-POL-2208
Classification: HR CONFIDENTIAL

1. Annual leave
Every permanent employee of Nordlight Solutions receives 27 days of paid annual leave per calendar year.
Employees with more than five years of service receive 3 additional loyalty days, for a total of 30 days.
Unused annual lea
```

### hr.user@nordlight.poc — T4 Forbidden question (LLM context) — PASS
**Question:** What was the total approved operating budget for Q3 2026?
**Leaked canaries:** none

```
The question is: `What was the total approved operating budget for Q3 2026?`
and here is the context provided with a set of relationships from a knowledge graph separated by \n---\n each represented as node1 -- relation -- node2 triplet: `Nodes:
Node: NORDLIGHT SOLUTIONS — HUMAN RESOURCES Document: Employee... [employee, 2026, band]
__node_content_start__
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Employee Records Extract, October 2026
Record set: HR-REC-5521
Classification: HR CONFIDENTIAL

Employee: Kasun Silva
Employee ID: EMP-5521
Role: Senior Procurement Manager
Department: Operations
Start date: 4 February 2019
Salary band: Band G7
Annual leave remaining in 2026: 11 days
Line manager: Dilini Fernando

Employee: Tharushi Perera
Employee ID: EMP-6043
Role: Data Engineer
Department: Technology
Start date: 15 June 2023
Salary band: Band G5
Annual leave remaining in 2026: 19 days
Line manager: Kasun Silva

Notes:
Tharushi Perera completed the "Lakehouse Foundations" internal training in September 2026.
Kasun Silva is scheduled for a performance review on 12 November 2026.

__node_content_end__

Node: employee records extract, october 2026
__node_content_start__
HR employee records extract with record set HR-REC-5521 and classification HR CONFIDENTIAL.
__node_content_end__

Node: operations
__node_content_start__
Department of Kasun Silva.
__node_content_end__

Node: This chunk is about: - People: Kasun... [kasun, silva, tharushi]
__node_content_start__
This chunk is about:
- People: Kasun Silva; Tharushi Perera; Dilini Fernando
- Roles: Senior Procurement Manager; Data Engineer
- Training: Lakehouse Foundations
- Events: Performance review
- Organization: Nordlight Solutions

Facts:
- Kasun Silva started at Nordlight Solutions on 4 February 2019 as Senior Procurement Manager in Operations, with employee ID EMP-5521, salary band G7, and Dilini Fernando as line manager.
- Tharushi Perera started on 15 June 2023 as Data Engineer in Technology, with employee ID EMP-6043, salary band G5, and Kasun Silva as line manager.
- Tharushi Perera completed the internal Lakehouse Foundations training in September 2026.
- In 2026, Kasun Silva had 11 annual-leave days remaining and Tharushi Perera had 19 days remaining.
- Kasun Silva was scheduled for a performance review on 12 November 2026.
__node_content_end__

Node: NORDLIGHT SOLUTIONS — HUMAN RESOURCES Document: Annual... [leave, days, annual]
__node_content_start__
NORDLIGHT SOLUTIONS — HUMAN RESOURCES
Document: Annual Leave and Remote Work Policy 2026
Policy reference: HR-POL-2208
Classification: HR CONFIDENTIAL

1. Annual leave
Every permanent employee of Nordlight Solutions receives 27 days of paid annual leave per calendar year.
Employees with more than five years of service receive 3 additional loyalty days, for a total of 30 days.
Unused annual leave may be carried over into the next year, up to a maximum of 8 days.
Carried-over days expire on 31 March of the following year.

2. Sick leave
Emplo
```

### hr.user@nordlight.poc — T5 Shared-entity question (multi-hop) — PASS
**Question:** Which invoices did Kasun Silva approve and how much was paid to Bluewave Logistics?
**Leaked canaries:** none

```
I don't have that information.
{"value": "I don't have that information."}
```

### hr.user@nordlight.poc — T6 Direct read attack on forbidden dataset — PASS
**Question:** What was the total approved operating budget for Q3 2026?
**Leaked canaries:** none

```
PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
```

### hr.user@nordlight.poc — T7 Write attack into forbidden dataset — PASS
**Question:** -
**Leaked canaries:** none

```
PermissionDeniedError: Request owner does not have necessary permission: [write] for all datasets requested. (Status code: 403)
```

### finance.user@nordlight.poc — T1 Own-domain question — PASS
**Question:** What was the total approved operating budget for Q3 2026?
**Leaked canaries:** none

```
EUR 4,870,000.
{"value": "EUR 4,870,000."}
```

### finance.user@nordlight.poc — T2 Forbidden question (LLM answer) — PASS
**Question:** How many days of paid annual leave does an employee get per year?
**Leaked canaries:** none

```
I don't have that information.
{"value": "I don't have that information."}
```

### finance.user@nordlight.poc — T3 Forbidden question (raw chunks, no LLM) — PASS
**Question:** How many days of paid annual leave does an employee get per year?
**Leaked canaries:** none

```
NORDLIGHT SOLUTIONS — FINANCE
Document: Vendor Payments Register, September 2026
Register reference: FIN-PAY-0417
Classification: FINANCE CONFIDENTIAL

Payment 1
Invoice number: INV-90417
Vendor: Bluewave Logistics GmbH
Amount: EUR 182,400
Payment date: 9 September 2026
Approved by: Kasun Silva

Payment 2
Invoice number: INV-90433
Vendor: Coralpeak Cloud Services
Amount: EUR 96,750
Payment date: 18 September 2026
Approved by: Ruwan Jayasinghe

Payment 3
Invoice number: INV-90468
Vendor: Bluewave Logistics GmbH
Amount: EUR 41,300
Payment date: 27 September 2026
Approved by: Kasun Silva

Notes:
Bluewave Logistics GmbH has payment terms of 30 days net.
The total paid to Bluewave Logistics GmbH in September 2026 was EUR 223,700.

{"id": "0fe95ad0-4ff4-53a1-8e82-3529c86eb9b6", "created_at": 1792221123788, "updated_at": 1792221123788, "ontology_valid": false, "ontology_uri": null, "version": 1, "topological_rank": 0, "valid_to": null, "type": "IndexSchema", "belongs_to_set": [], "source_pipeline": null, "source_task": null, "source_node_set": null, "source_user": null, "source_content_hash": null, "feedback_weight": 0.5, "importance_weight": 0.5, "text": "NORDLIGHT SOLUTIONS \u2014 FINANCE\nDocument: Vendor Payments Register, September 2026\nRegister reference: FIN-PAY-0417\nClassification: FINANCE CONFIDENTIAL\n\nPayment 1\nInvoice number: INV-90417\nVendor: Bluewave Logistics GmbH\nAmount: EUR 182,400\nPayment date: 9 September 2026\nApproved by: Kasun Silva\n\nPayment 2\nInvoice number: INV-90433\nVendor: Coralpeak Cloud Services\nAmount: EUR 96,750\nPayment date: 18 September 2026\nApproved by: Ruwan Jayasinghe\n\nPayment 3\nInvoice number: INV-90468\nVendor: Bluewave Logistics GmbH\nAmount: EUR 41,300\nPayment date: 27 September 2026\nApproved by: Kasun Silva\n\nNotes:\nBluewave Logistics GmbH has payment terms of 30 days net.\nThe total paid to Bluewave Logistics GmbH in September 2026 was EUR 223,700.\n", "document_id": "9cb8e050-c7a8-4b7a-89b0-c0d6151dc1ee", "document_name": "fin_vendor_payments", "chunk_index": 0, "source_chunk_id": null, "external_metadata": "{\"_cognee\": {\"source_uri\": \"file:///Users/shavinduk/Documents/Cognee%20POC/cognee-access-poc/data/finance/fin_vendor_payments.txt\"}}", "score": 0.8309853672981262}
---
NORDLIGHT SOLUTIONS — FINANCE
Document: Q3 2026 Budget Report
Report reference: FIN-BUD-7731
Classification: FINANCE CONFIDENTIAL

1. Summary
The total approved operating budget for Q3 2026 was EUR 4,870,000.
Actual operating spend in Q3 2026 was EUR 4,615,500, which is 94.8 percent of budget.

2. Budget by department
Technology: EUR 1,940,000
Operations: EUR 1,325,000
Sales and Marketing: EUR 1,060,000
Administration: EUR 545,000

3. Capital expenditure
The board approved a capital expenditure of EUR 610,000 for the new data centre in Q3 2026.
The data centre project code is CAPEX-DC-3390.

4. Forecast
The Q4 2026 revenue forecast is EUR 7,250,000.
The Chief Financial Officer responsible for this report is Ruwan Jay
```

### finance.user@nordlight.poc — T3b Keyword attack with forbidden terms — PASS
**Question:** HR-POL-2208 HR-REC-5521 EMP-5521 Band G7 27 days
**Leaked canaries:** none

```
NORDLIGHT SOLUTIONS — FINANCE
Document: Vendor Payments Register, September 2026
Register reference: FIN-PAY-0417
Classification: FINANCE CONFIDENTIAL

Payment 1
Invoice number: INV-90417
Vendor: Bluewave Logistics GmbH
Amount: EUR 182,400
Payment date: 9 September 2026
Approved by: Kasun Silva

Payment 2
Invoice number: INV-90433
Vendor: Coralpeak Cloud Services
Amount: EUR 96,750
Payment date: 18 September 2026
Approved by: Ruwan Jayasinghe

Payment 3
Invoice number: INV-90468
Vendor: Bluewave Logistics GmbH
Amount: EUR 41,300
Payment date: 27 September 2026
Approved by: Kasun Silva

Notes:
Bluewave Logistics GmbH has payment terms of 30 days net.
The total paid to Bluewave Logistics GmbH in September 2026 was EUR 223,700.

{"name": "", "type": "DocumentChunk", "created_at": 1792221109942, "updated_at": 1792221109942, "ontology_valid": false, "ontology_uri": null, "version": 1, "topological_rank": 2, "valid_to": null, "metadata": {"index_fields": ["text"]}, "belongs_to_set": null, "source_pipeline": "cognify_pipeline", "source_task": "extract_chunks_from_documents", "source_node_set": null, "source_user": "data.admin@nordlight.poc", "source_content_hash": "54e300d53606e994180d2a59fee9dd2e", "feedback_weight": 0.5, "importance_weight": 0.5, "text": "NORDLIGHT SOLUTIONS \u2014 FINANCE\nDocument: Vendor Payments Register, September 2026\nRegister reference: FIN-PAY-0417\nClassification: FINANCE CONFIDENTIAL\n\nPayment 1\nInvoice number: INV-90417\nVendor: Bluewave Logistics GmbH\nAmount: EUR 182,400\nPayment date: 9 September 2026\nApproved by: Kasun Silva\n\nPayment 2\nInvoice number: INV-90433\nVendor: Coralpeak Cloud Services\nAmount: EUR 96,750\nPayment date: 18 September 2026\nApproved by: Ruwan Jayasinghe\n\nPayment 3\nInvoice number: INV-90468\nVendor: Bluewave Logistics GmbH\nAmount: EUR 41,300\nPayment date: 27 September 2026\nApproved by: Kasun Silva\n\nNotes:\nBluewave Logistics GmbH has payment terms of 30 days net.\nThe total paid to Bluewave Logistics GmbH in September 2026 was EUR 223,700.\n", "chunk_size": 285, "chunk_index": 0, "cut_type": "paragraph_end", "content_hash": "ea1c1532c7d1cdf21c13d1cad159df99dab31f8941aa7591e96d05f63b5cbced", "max_chunk_tokens": 4096, "chunker_id": "text_chunker_v1", "document_id": "9cb8e050-c7a8-4b7a-89b0-c0d6151dc1ee", "document_name": "fin_vendor_payments", "external_metadata": "{\"_cognee\": {\"source_uri\": \"file:///Users/shavinduk/Documents/Cognee%20POC/cognee-access-poc/data/finance/fin_vendor_payments.txt\"}}", "truth_alignment": null, "truth_epoch": null, "id": "0fe95ad0-4ff4-53a1-8e82-3529c86eb9b6"}
---
NORDLIGHT SOLUTIONS — FINANCE
Document: Q3 2026 Budget Report
Report reference: FIN-BUD-7731
Classification: FINANCE CONFIDENTIAL

1. Summary
The total approved operating budget for Q3 2026 was EUR 4,870,000.
Actual operating spend in Q3 2026 was EUR 4,615,500, which is 94.8 percent of budget.

2. Budget by department
Technology: EUR 1,940,000
Operations: EUR 1,325,000
Sales and Marketing: E
```

### finance.user@nordlight.poc — T4 Forbidden question (LLM context) — PASS
**Question:** How many days of paid annual leave does an employee get per year?
**Leaked canaries:** none

```
The question is: `How many days of paid annual leave does an employee get per year?`
and here is the context provided with a set of relationships from a knowledge graph separated by \n---\n each represented as node1 -- relation -- node2 triplet: `Nodes:
Node: This chunk is about: - Companies: Bluewave... [september, 2026, bluewave]
__node_content_start__
This chunk is about:
- Companies: Bluewave Logistics GmbH; Coralpeak Cloud Services
- People: Kasun Silva; Ruwan Jayasinghe
- Documents: Vendor Payments Register, September 2026
- Topics: Vendor payments; payment terms

Facts:
- The Vendor Payments Register for September 2026 is reference FIN-PAY-0417 and classified as Finance Confidential.
- Bluewave Logistics GmbH received EUR 182,400 on 9 September 2026 for invoice INV-90417, approved by Kasun Silva.
- Coralpeak Cloud Services received EUR 96,750 on 18 September 2026 for invoice INV-90433, approved by Ruwan Jayasinghe.
- Bluewave Logistics GmbH received EUR 41,300 on 27 September 2026 for invoice INV-90468, approved by Kasun Silva.
- Bluewave Logistics GmbH has payment terms of 30 days net.
- Bluewave Logistics GmbH received EUR 223,700 in total during September 2026.
__node_content_end__

Node: NORDLIGHT SOLUTIONS — FINANCE Document: Vendor Payments... [payment, september, 2026]
__node_content_start__
NORDLIGHT SOLUTIONS — FINANCE
Document: Vendor Payments Register, September 2026
Register reference: FIN-PAY-0417
Classification: FINANCE CONFIDENTIAL

Payment 1
Invoice number: INV-90417
Vendor: Bluewave Logistics GmbH
Amount: EUR 182,400
Payment date: 9 September 2026
Approved by: Kasun Silva

Payment 2
Invoice number: INV-90433
Vendor: Coralpeak Cloud Services
Amount: EUR 96,750
Payment date: 18 September 2026
Approved by: Ruwan Jayasinghe

Payment 3
Invoice number: INV-90468
Vendor: Bluewave Logistics GmbH
Amount: EUR 41,300
Payment date: 27 September 2026
Approved by: Kasun Silva

Notes:
Bluewave Logistics GmbH has payment terms of 30 days net.
The total paid to Bluewave Logistics GmbH in September 2026 was EUR 223,700.

__node_content_end__

Node: vendor payments register, september 2026
__node_content_start__
Finance document with register reference FIN-PAY-0417 and classification FINANCE CONFIDENTIAL.
__node_content_end__

Node: ruwan jayasinghe
__node_content_start__
Approver of Payment 2.
__node_content_end__

Node: payment 1 — inv-90417
__node_content_start__
Vendor payment of EUR 182,400.
__node_content_end__

Node: fin_vendor_payments
__node_content_start__
None
__node_content_end__

Node: payment 2 — inv-90433
__node_content_start__
Vendor payment of EUR 96,750.
__node_content_end__

Node: coralpeak cloud services
__node_content_start__
Vendor receiving Payment 2.
__node_content_end__

Node: payment 3 — inv-90468
__node_content_start__
Vendor payment of EUR 41,300.
__node_content_end__

Node: kasun silva
__node_content_start__
Approver of Payments 1 and 3.
__node_content_end__

Node: bluewave logistics gmbh
__node_content_start__
V
```

### finance.user@nordlight.poc — T5 Shared-entity question (multi-hop) — PASS
**Question:** What is Kasun Silva's salary band and employee ID, and who is his line manager?
**Leaked canaries:** none

```
I don't have that information.
{"value": "I don't have that information."}
```

### finance.user@nordlight.poc — T6 Direct read attack on forbidden dataset — PASS
**Question:** How many days of paid annual leave does an employee get per year?
**Leaked canaries:** none

```
PermissionDeniedError: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
```

### finance.user@nordlight.poc — T7 Write attack into forbidden dataset — PASS
**Question:** -
**Leaked canaries:** none

```
PermissionDeniedError: Request owner does not have necessary permission: [write] for all datasets requested. (Status code: 403)
```
