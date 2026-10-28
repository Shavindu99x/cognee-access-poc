# Northwind CSV test

Five files were stored in the datasets named by the files: `northwind_hr`, `northwind_finance`, `northwind_legal`, `northwind_marketing`, and `northwind_employees_master`.
A CSV is stored as one row node per employee. Chunk search finds no document chunks in that graph. The retrieval below is Cognee hybrid search, which reads the row nodes. Cognee returns one result per dataset, and each result includes neighboring rows.
Mia Silva, EMP0037, is in HR, finance, and legal. She is not in marketing. The master file lists her departments as FIN;HR;LEG.

Checks passed: 46 of 46.

## Cognee retrieval for the person who can read HR, finance, and legal

Question: What job title does EMP0037 hold?

Cognee searched each graph on its own and returned one result per dataset.

### Raw result

`northwind_hr` (769 characters)

Table: hr
Columns:
  - employee_id (TEXT)
  - first_name (TEXT)
  - last_name (TEXT)
  - email (TEXT)
  - dept_code (TEXT)
  - department (TEXT)
  - job_title (TEXT)
  - role_type (TEXT)
  - allocation_pct (BIGINT)
  - dept_start_date (TEXT)
  - location (TEXT)
  - employment_type (TEXT)
  - hire_date (TEXT)
  - is_active (BOOLEAN)
  - _dlt_load_id (TEXT)
  - _dlt_id (VARCHAR(128))
  - manager_id (TEXT)

Row Data:
  employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-02-14
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0004

`northwind_finance` (765 characters)

Table: finance
Columns:
  - employee_id (TEXT)
  - first_name (TEXT)
  - last_name (TEXT)
  - email (TEXT)
  - dept_code (TEXT)
  - department (TEXT)
  - job_title (TEXT)
  - role_type (TEXT)
  - allocation_pct (BIGINT)
  - dept_start_date (TEXT)
  - location (TEXT)
  - employment_type (TEXT)
  - hire_date (TEXT)
  - is_active (BOOLEAN)
  - _dlt_load_id (TEXT)
  - _dlt_id (VARCHAR(128))
  - manager_id (TEXT)

Row Data:
  employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: Controller
  role_type: Primary
  allocation_pct: 50
  dept_start_date: 2023-08-03
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0001

`northwind_legal` (762 characters)

Table: legal
Columns:
  - employee_id (TEXT)
  - first_name (TEXT)
  - last_name (TEXT)
  - email (TEXT)
  - dept_code (TEXT)
  - department (TEXT)
  - job_title (TEXT)
  - role_type (TEXT)
  - allocation_pct (BIGINT)
  - dept_start_date (TEXT)
  - location (TEXT)
  - employment_type (TEXT)
  - hire_date (TEXT)
  - is_active (BOOLEAN)
  - _dlt_load_id (TEXT)
  - _dlt_id (VARCHAR(128))
  - manager_id (TEXT)

Row Data:
  employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: Paralegal
  role_type: Secondary
  allocation_pct: 20
  dept_start_date: 2024-06-09
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0005

### Dispatcher answer

In northwind_hr, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-02-14
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0004 In northwind_finance, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: Controller
  role_type: Primary
  allocation_pct: 50
  dept_start_date: 2023-08-03
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0001 In northwind_legal, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: Paralegal
  role_type: Secondary
  allocation_pct: 20
  dept_start_date: 2024-06-09
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0005

## HR person, same question, HR dataset only

In northwind_hr, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-02-14
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0004

## Roster reader, master dataset

In northwind_employees_master, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  hire_date: 2023-08-03
  location: Hamburg
  employment_type: Full-time
  dept_count: 3
  departments: FIN;HR;LEG

## Single department

### hr reader

Question: What job title does EMP0011 hold?

Cognee opened: northwind_hr. Raw size: northwind_hr 781 characters. Dispatcher mode: direct.

In northwind_hr, the retrieved record says: employee_id: EMP0011
  first_name: Mei
  last_name: Neumann
  email: mei.neumann@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Business Partner
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2021-06-22
  location: Hamburg
  employment_type: Full-time
  hire_date: 2021-06-22
  is_active: 1
  manager_id: EMP0004

### finance reader

Question: What job title does EMP0001 hold?

Cognee opened: northwind_finance. Raw size: northwind_finance 761 characters. Dispatcher mode: direct.

In northwind_finance, the retrieved record says: employee_id: EMP0001
  first_name: Noah
  last_name: Schmidt
  email: noah.schmidt@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: CFO
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2023-04-26
  location: Munich
  employment_type: Full-time
  hire_date: 2023-04-26
  is_active: 1
  manager_id: None

### legal reader

Question: What job title does EMP0005 hold?

Cognee opened: northwind_legal. Raw size: northwind_legal 778 characters. Dispatcher mode: direct.

In northwind_legal, the retrieved record says: employee_id: EMP0005
  first_name: Kasun
  last_name: Zimmermann
  email: kasun.zimmermann@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: General Counsel
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2017-06-21
  location: Colombo
  employment_type: Full-time
  hire_date: 2017-06-21
  is_active: 1
  manager_id: None

### marketing reader

Question: What job title does EMP0003 hold?

Cognee opened: northwind_marketing. Raw size: northwind_marketing 776 characters. Dispatcher mode: direct.

In northwind_marketing, the retrieved record says: employee_id: EMP0003
  first_name: Jan
  last_name: Müller
  email: jan.mueller@northwind-mock.com
  dept_code: MKT
  department: Marketing
  job_title: Head of Marketing
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2015-05-03
  location: Berlin
  employment_type: Full-time
  hire_date: 2015-05-03
  is_active: 1
  manager_id: None

### hr reader

Question: What job title does EMP0004 hold?

Cognee opened: northwind_hr. Raw size: northwind_hr 765 characters. Dispatcher mode: direct.

In northwind_hr, the retrieved record says: employee_id: EMP0004
  first_name: Priya
  last_name: Wang
  email: priya.wang@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: Head of HR
  role_type: Primary
  allocation_pct: 60
  dept_start_date: 2015-04-19
  location: Remote
  employment_type: Full-time
  hire_date: 2015-04-19
  is_active: 0
  manager_id: None

### hr reader

Question: What job title does EMP0003 hold?

Cognee opened: none. Raw size: no dataset opened. Dispatcher mode: none.

That is not in the information you can access.

### marketing reader

Question: What job title does EMP0011 hold?

Cognee opened: none. Raw size: no dataset opened. Dispatcher mode: none.

That is not in the information you can access.

### finance reader

Question: What does hr say about EMP0011?

Cognee opened: none. Raw size: no dataset opened. Dispatcher mode: closed.

You do not have access.

### legal reader, with the finance dataset also requested

Question: What job title does EMP0005 hold?

Cognee opened: northwind_legal. Raw size: northwind_legal 778 characters. Dispatcher mode: direct.

In northwind_legal, the retrieved record says: employee_id: EMP0005
  first_name: Kasun
  last_name: Zimmermann
  email: kasun.zimmermann@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: General Counsel
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2017-06-21
  location: Colombo
  employment_type: Full-time
  hire_date: 2017-06-21
  is_active: 1
  manager_id: None

### roster reader

Question: Which departments include EMP0008?

Cognee opened: northwind_employees_master. Raw size: northwind_employees_master 513 characters. Dispatcher mode: direct.

In northwind_employees_master, the retrieved record says: employee_id: EMP0008
  first_name: Marie
  last_name: Fischer
  email: marie.fischer@northwind-mock.com
  hire_date: 2019-01-10
  location: Munich
  employment_type: Full-time
  dept_count: 3
  departments: MKT;LEG;FIN

## Several departments

### hr, finance, and legal reader

Question: What job title does EMP0004 hold?

Cognee opened: northwind_hr, northwind_finance. Raw size: northwind_hr 765 characters, northwind_finance 768 characters. Dispatcher mode: combined.

In northwind_hr, the retrieved record says: employee_id: EMP0004
  first_name: Priya
  last_name: Wang
  email: priya.wang@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: Head of HR
  role_type: Primary
  allocation_pct: 60
  dept_start_date: 2015-04-19
  location: Remote
  employment_type: Full-time
  hire_date: 2015-04-19
  is_active: 0
  manager_id: None In northwind_finance, the retrieved record says: employee_id: EMP0004
  first_name: Priya
  last_name: Wang
  email: priya.wang@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: Accountant
  role_type: Secondary
  allocation_pct: 40
  dept_start_date: 2017-04-21
  location: Remote
  employment_type: Full-time
  hire_date: 2015-04-19
  is_active: 1
  manager_id: EMP0001

### hr, finance, and legal reader

Question: What job title does EMP0006 hold?

Cognee opened: northwind_hr, northwind_finance. Raw size: northwind_hr 771 characters, northwind_finance 771 characters. Dispatcher mode: combined.

In northwind_hr, the retrieved record says: employee_id: EMP0006
  first_name: Anna
  last_name: Becker
  email: anna.becker@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Primary
  allocation_pct: 70
  dept_start_date: 2022-10-30
  location: Colombo
  employment_type: Full-time
  hire_date: 2022-10-30
  is_active: 1
  manager_id: EMP0004 In northwind_finance, the retrieved record says: employee_id: EMP0006
  first_name: Anna
  last_name: Becker
  email: anna.becker@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: Controller
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2022-11-08
  location: Colombo
  employment_type: Full-time
  hire_date: 2022-10-30
  is_active: 1
  manager_id: EMP0001

### hr, finance, and legal reader

Question: What job title does EMP0008 hold?

Cognee opened: northwind_finance, northwind_legal. Raw size: northwind_finance 777 characters, northwind_legal 778 characters. Dispatcher mode: combined.

In northwind_finance, the retrieved record says: employee_id: EMP0008
  first_name: Marie
  last_name: Fischer
  email: marie.fischer@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: AP Specialist
  role_type: Secondary
  allocation_pct: 20
  dept_start_date: 2021-05-12
  location: Munich
  employment_type: Full-time
  hire_date: 2019-01-10
  is_active: 1
  manager_id: EMP0001 In northwind_legal, the retrieved record says: employee_id: EMP0008
  first_name: Marie
  last_name: Fischer
  email: marie.fischer@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: Compliance Officer
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2019-06-20
  location: Munich
  employment_type: Full-time
  hire_date: 2019-01-10
  is_active: 1
  manager_id: EMP0005

### hr, finance, and legal reader

Question: What job title does EMP0035 hold?

Cognee opened: northwind_hr, northwind_finance, northwind_legal. Raw size: northwind_hr 781 characters, northwind_finance 775 characters, northwind_legal 773 characters. Dispatcher mode: combined.

In northwind_hr, the retrieved record says: employee_id: EMP0035
  first_name: Noah
  last_name: Neumann
  email: noah.neumann@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Business Partner
  role_type: Primary
  allocation_pct: 50
  dept_start_date: 2024-11-08
  location: Munich
  employment_type: Full-time
  hire_date: 2024-11-08
  is_active: 1
  manager_id: EMP0004 In northwind_finance, the retrieved record says: employee_id: EMP0035
  first_name: Noah
  last_name: Neumann
  email: noah.neumann@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: AP Specialist
  role_type: Secondary
  allocation_pct: 20
  dept_start_date: 2025-09-06
  location: Munich
  employment_type: Full-time
  hire_date: 2024-11-08
  is_active: 1
  manager_id: EMP0001 In northwind_legal, the retrieved record says: employee_id: EMP0035
  first_name: Noah
  last_name: Neumann
  email: noah.neumann@northwind-mock.com
  dept_code: LEG
  department: Legal
  job_title: Privacy Officer
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-12-25
  location: Munich
  employment_type: Full-time
  hire_date: 2024-11-08
  is_active: 0
  manager_id: EMP0005

### hr, finance, and legal reader

Question: What job title does EMP0001 hold?

Cognee opened: northwind_finance. Raw size: northwind_finance 761 characters. Dispatcher mode: direct.

In northwind_finance, the retrieved record says: employee_id: EMP0001
  first_name: Noah
  last_name: Schmidt
  email: noah.schmidt@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: CFO
  role_type: Primary
  allocation_pct: 100
  dept_start_date: 2023-04-26
  location: Munich
  employment_type: Full-time
  hire_date: 2023-04-26
  is_active: 1
  manager_id: None

### hr, finance, and legal reader

Question: What job title does EMP0003 hold?

Cognee opened: none. Raw size: no dataset opened. Dispatcher mode: none.

That is not in the information you can access.

### hr, finance, and legal reader

Question: What does marketing say about EMP0003?

Cognee opened: none. Raw size: no dataset opened. Dispatcher mode: closed.

You do not have access.

### hr, finance, and legal reader

Question: What job title does EMP0004 hold? Keep both department records when they disagree.

Cognee opened: northwind_hr, northwind_finance. Raw size: northwind_hr 765 characters, northwind_finance 768 characters. Dispatcher mode: combined.

In northwind_hr, the retrieved record says: employee_id: EMP0004
  first_name: Priya
  last_name: Wang
  email: priya.wang@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: Head of HR
  role_type: Primary
  allocation_pct: 60
  dept_start_date: 2015-04-19
  location: Remote
  employment_type: Full-time
  hire_date: 2015-04-19
  is_active: 0
  manager_id: None In northwind_finance, the retrieved record says: employee_id: EMP0004
  first_name: Priya
  last_name: Wang
  email: priya.wang@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: Accountant
  role_type: Secondary
  allocation_pct: 40
  dept_start_date: 2017-04-21
  location: Remote
  employment_type: Full-time
  hire_date: 2015-04-19
  is_active: 1
  manager_id: EMP0001

### hr and finance reader, after legal read was removed

Question: What job title does EMP0035 hold?

Cognee opened: northwind_hr, northwind_finance. Raw size: northwind_hr 781 characters, northwind_finance 775 characters. Dispatcher mode: combined.

In northwind_hr, the retrieved record says: employee_id: EMP0035
  first_name: Noah
  last_name: Neumann
  email: noah.neumann@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Business Partner
  role_type: Primary
  allocation_pct: 50
  dept_start_date: 2024-11-08
  location: Munich
  employment_type: Full-time
  hire_date: 2024-11-08
  is_active: 1
  manager_id: EMP0004 In northwind_finance, the retrieved record says: employee_id: EMP0035
  first_name: Noah
  last_name: Neumann
  email: noah.neumann@northwind-mock.com
  dept_code: FIN
  department: Finance
  job_title: AP Specialist
  role_type: Secondary
  allocation_pct: 20
  dept_start_date: 2025-09-06
  location: Munich
  employment_type: Full-time
  hire_date: 2024-11-08
  is_active: 1
  manager_id: EMP0001

## Checks

- PASS — hr file stays in its own dataset: clean
- PASS — finance file stays in its own dataset: clean
- PASS — legal file stays in its own dataset: clean
- PASS — marketing file stays in its own dataset: clean
- PASS — employees_master file stays in its own dataset: clean
- PASS — owner is not a superuser: northwind.admin@northwind.poc
- PASS — hr reader is not a superuser: hr.user@northwind.poc
- PASS — finance reader is not a superuser: finance.user@northwind.poc
- PASS — legal reader is not a superuser: legal.user@northwind.poc
- PASS — marketing reader is not a superuser: marketing.user@northwind.poc
- PASS — span reader is not a superuser: hr.finance.legal.user@northwind.poc
- PASS — roster reader is not a superuser: roster.user@northwind.poc
- PASS — Mia Silva's row is stored in each department graph, and the ids are not an edge: {"northwind_hr": {"id": "6798c8bb-9bfc-5c6c-880d-95a70b75207d", "matched": "DltRow"}, "northwind_finance": {"id": "c0e889d6-2e46-5377-b00b-2fa3e643c24e", "matched": "DltRow"}, "northwind_legal": {"id": "a3b72e94-055a-586e-a77a-28be6ad425ca", "matched": "DltRow"}}
- PASS — chunk search has no document chunks for a CSV dataset: NoDataError: No searchable memory in dataset 'northwind_hr' (id: f923600f-fa65-5713-ae97-a1cbc5556734): No valid chunks loaded during initialization. (Status code: 404)
- PASS — hr person receives only Mia Silva's HR row: In northwind_hr, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-02-14
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0004
- PASS — hr person is denied the finance dataset: You do not have access.
- PASS — hr person does not receive a finance-only employee: That is not in the information you can access.
- PASS — a closed finance id does not cancel the HR answer: In northwind_hr, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  dept_code: HR
  department: Human Resources
  job_title: HR Manager
  role_type: Secondary
  allocation_pct: 30
  dept_start_date: 2025-02-14
  location: Hamburg
  employment_type: Full-time
  hire_date: 2023-08-03
  is_active: 1
  manager_id: EMP0004
- PASS — cognee refuses the whole call when a closed dataset is included: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
- PASS — cognee returns Mia Silva separately from HR, finance, and legal: northwind_finance, northwind_hr, northwind_legal
- PASS — dispatcher keeps Mia Silva's three job titles and drops the other rows: mode=combined opened=['northwind_hr', 'northwind_finance', 'northwind_legal']
- PASS — an unnamed closed id does not add a denial: combined
- PASS — the roster reader receives the master row and not a department job title: In northwind_employees_master, the retrieved record says: employee_id: EMP0037
  first_name: Mia
  last_name: Silva
  email: mia.silva@northwind-mock.com
  hire_date: 2023-08-03
  location: Hamburg
  employment_type: Full-time
  dept_count: 3
  departments: FIN;HR;LEG
- PASS — the owner is not used to answer: Questions run as a reader. The owner is not used to answer.
- PASS — hr reader: What job title does EMP0011 hold?: mode=direct opened=['northwind_hr']
- PASS — finance reader: What job title does EMP0001 hold?: mode=direct opened=['northwind_finance']
- PASS — legal reader: What job title does EMP0005 hold?: mode=direct opened=['northwind_legal']
- PASS — marketing reader: What job title does EMP0003 hold?: mode=direct opened=['northwind_marketing']
- PASS — hr reader: What job title does EMP0004 hold?: mode=direct opened=['northwind_hr']
- PASS — hr reader: What job title does EMP0003 hold?: mode=none opened=[]
- PASS — marketing reader: What job title does EMP0011 hold?: mode=none opened=[]
- PASS — finance reader: What does hr say about EMP0011?: mode=closed opened=[]
- PASS — legal reader, with the finance dataset also requested: What job title does EMP0005 hold?: mode=direct opened=['northwind_legal']
- PASS — hr, finance, and legal reader: What job title does EMP0004 hold?: mode=combined opened=['northwind_hr', 'northwind_finance']
- PASS — hr, finance, and legal reader: What job title does EMP0006 hold?: mode=combined opened=['northwind_hr', 'northwind_finance']
- PASS — hr, finance, and legal reader: What job title does EMP0008 hold?: mode=combined opened=['northwind_finance', 'northwind_legal']
- PASS — hr, finance, and legal reader: What job title does EMP0035 hold?: mode=combined opened=['northwind_hr', 'northwind_finance', 'northwind_legal']
- PASS — hr, finance, and legal reader: What job title does EMP0001 hold?: mode=direct opened=['northwind_finance']
- PASS — hr, finance, and legal reader: What job title does EMP0003 hold?: mode=none opened=[]
- PASS — hr, finance, and legal reader: What does marketing say about EMP0003?: mode=closed opened=[]
- PASS — roster reader: Which departments include EMP0008?: mode=direct opened=['northwind_employees_master']
- PASS — hr, finance, and legal reader: What job title does EMP0004 hold? Keep both department records when they disagree.: mode=combined opened=['northwind_hr', 'northwind_finance']
- PASS — both department records stay when they disagree: is_active values: 0, 1
- PASS — the answer is not stored: absent
- PASS — hr and finance reader, after legal read was removed: What job title does EMP0035 hold?: mode=combined opened=['northwind_hr', 'northwind_finance']
- PASS — cognee still refuses legal after read is removed: PermissionDeniedError: Request owner does not have necessary permission: [read] for all datasets requested. (Status code: 403)
