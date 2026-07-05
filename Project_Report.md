# Mini Project Report
## Database Systems Lab (CSS 2212)

# Placement Management System

---

## SUBMITTED BY

| Student Name | Reg. No. | Roll No. | Section |
|---|---|---|---|
| *(Your Name)* | *(Your Reg. No.)* | *(Your Roll No.)* | *(Your Section)* |
| *(Partner Name)* | *(Reg. No.)* | *(Roll No.)* | *(Section)* |

**School of Computer Engineering**
**Manipal Institute of Technology, Manipal.**
**April 2026**

---

## CERTIFICATE

**DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING**

**Manipal**

This is to certify that the project titled **Placement Management System** is a record of the bonafide work done by *(Your Name)* (Reg. No. \_\_\_\_\_\_\_\_\_\_) and *(Partner Name)* (Reg. No. \_\_\_\_\_\_\_\_\_\_) submitted in partial fulfilment of the requirements for the award of the Degree of Bachelor of Technology (B.Tech.) in \_\_\_\_\_\_\_\_\_\_ Engineering of Manipal Institute of Technology, Manipal, Karnataka (A Constituent Institute of Manipal Academy of Higher Education), during the academic year 2025–2026.

**Name and Signature of Examiners:**

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## ABSTRACT

The Placement Management System is a web application that automates the complete lifecycle of campus placement operations for a college. Built using **Flask** (Python) as the web backend and **MySQL 8.x** as the relational database engine, the system handles student registration, placement drive management, application tracking, selection rounds, round-wise results, and role-based access for students and Training & Placement Officers (TPO) through a single integrated platform.

The database schema, contained in `schema.sql`, is designed to satisfy all concepts prescribed in the CSS 2212 Database Systems Lab manual at MIT Manipal. It comprises **eleven normalised tables** that collectively achieve Third Normal Form (3NF). The schema includes **two database views** for complex multi-table joins, **two triggers** that enforce business rules and automate status history logging, and **one stored procedure** that enforces the college's one-student-one-company placement policy entirely at the database level.

The application follows a two-tier architecture: the Flask presentation layer communicates with MySQL via the `mysql-connector-python` driver, using parameterised queries for all database access to prevent SQL injection. The system supports two user roles — **Student** and **Placement Officer** — each with role-specific dashboards and access controls. The project demonstrates a complete integration of relational database theory with a working, deployable web application.

---

## CHAPTER 1: INTRODUCTION

### 1.1 Background

Campus placement management is one of the most data-intensive processes in any engineering college. Coordinating placement drives across multiple companies, tracking hundreds of student applications across different selection rounds, enforcing eligibility criteria (CGPA cutoffs, branch restrictions), ensuring the one-student-one-offer policy, and maintaining a complete audit trail of status changes are all tasks that demand precision and guaranteed consistency. When managed through disconnected spreadsheets, these operations suffer from update anomalies, missed eligibility checks, and the complete absence of an audit trail.

A well-designed relational database management system (RDBMS) with referential integrity constraints, normalised tables, and database-level automation through triggers and stored procedures provides the ideal foundation. This project demonstrates that approach in a working, deployable Flask web application backed by a MySQL 8.x database that embodies all the SQL concepts from Labs 1 through 11 of the CSS 2212 course.

### 1.2 Scope

The system covers the following functional areas:

1. **Student registration & authentication**: Personal data, branch, CGPA, backlogs, and skill selection stored across normalised tables with proper constraints.
2. **Skill management**: Skills stored as a master lookup table with a junction table (`Student_Skills`) linking students to their skills — resolving the multi-valued dependency.
3. **Company & location management**: Companies linked to locations via foreign keys. TPO can add or delete companies through the interface.
4. **Placement drive posting**: Drives linked to companies and officers with eligibility criteria (CGPA, branches) enforced at application time.
5. **Application tracking**: Students apply to drives; eligibility is verified server-side. Application status progresses through Applied → Shortlisted → In Process → Selected/Rejected/Withdrawn.
6. **Selection rounds & results**: Per-drive rounds with per-student results (Pass/Fail/Pending) with upsert capability.
7. **Status history audit trail**: `Application_Status_History` table written exclusively by database triggers — never by application code.
8. **One-student-one-company policy**: A stored procedure (`sp_update_status`) enforces the placement policy: when a student is marked "Selected", all their other active applications are automatically withdrawn.
9. **Role-based access**: Students see dashboards and drives; TPO officers see management tools. Access enforced at route level.

### 1.3 Technology Stack

| Component | Technology | Version / Detail |
|---|---|---|
| Database Engine | MySQL | 8.x — InnoDB engine, utf8mb4 charset |
| Application Layer | Flask | Python micro web framework |
| Template Engine | Jinja2 | Server-side HTML rendering |
| DB Driver | mysql-connector-python | PEP 249 compliant MySQL driver |
| Language | Python | 3.x |
| Front-End | HTML5 + CSS3 + Bootstrap 5 | Responsive UI with glassmorphism & animations |
| DB Script | `schema.sql` | 11 tables, 2 views, 2 triggers, 1 stored procedure |

---

## CHAPTER 2: PROBLEM STATEMENT & OBJECTIVES

### 2.1 Problem Statement

Most colleges without a dedicated placement portal rely on spreadsheets and notice boards to manage placement data. This approach introduces several critical problems:

1. **Data Inconsistency**: A student's application status, eligibility data, and company drive details exist in separate sheets with no referential link. Updating one without the other creates inconsistencies that go undetected.
2. **No Business Rule Enforcement**: Nothing prevents a student with insufficient CGPA from applying to a drive, or a student already placed from applying to another company. Validation, if any, exists only in manual checks that can be bypassed.
3. **No Audit Trail**: When an application status changes from "Shortlisted" to "Selected", there is no automatic record of who changed it, what the old status was, or when the change occurred.
4. **Lack of Role-Based Access**: Any user with sheet access can modify any record. There is no concept of a TPO who manages drives versus a Student who can only view and apply.
5. **Placement Policy Violations**: The one-student-one-company policy must be enforced manually. If a student gets selected by Company A, the TPO must remember to manually withdraw all other applications — an error-prone process.
6. **Skill Tracking Inflexibility**: Storing skills as a comma-separated string in the student table violates First Normal Form and makes skill-based queries impossible.

This project addresses all six problems through proper relational database design, named constraint enforcement at the database level, database-level automation via triggers and a stored procedure, and a Flask web interface that exposes only role-appropriate operations.

### 2.2 Objectives

1. Design and implement a fully normalised relational database schema (1NF through 3NF) for the campus placement management domain.
2. Demonstrate all SQL constraint types: PRIMARY KEY, UNIQUE, NOT NULL, DEFAULT, CHECK, FOREIGN KEY (with CASCADE and RESTRICT), and ENUM.
3. Implement two database views using multi-table JOINs for reusable drive listing and application detail queries.
4. Implement two database triggers to automate audit logging of application status changes entirely at the database level.
5. Implement one stored procedure (`sp_update_status`) that enforces the one-student-one-company placement policy at the database level.
6. Build a Flask web application that connects to MySQL via `mysql-connector-python`, using parameterised queries for all database access.
7. Implement role-based access control at the application level (Student vs. TPO Officer dashboards).

---

## CHAPTER 3: METHODOLOGY

### 3.1 Database Design Methodology

#### 3.1.1 Entity Identification

The real-world entities in a campus placement domain were identified: **Student**, **Company**, **Location**, **Placement Officer**, **Placement Drive**, **Application**, **Selection Round**, **Round Result**, **Skill**, and **Application Status History**. Each entity became a candidate table.

#### 3.1.2 Attribute Definition and 1NF

For each entity, attributes were made atomic. A critical 1NF violation in the naive design was the storage of student skills as a comma-separated string in the student table — a repeating group. This was eliminated by creating the `Skills` master table and the `Student_Skills` junction table with one row per (student, skill) pair. Similarly, eligible branches in a drive are stored as a comma-separated string for simplicity, but queried via string operations.

#### 3.1.3 Normalisation (2NF, 3NF)

The schema was normalised progressively. All tables use single-column surrogate primary keys, making partial dependencies structurally impossible (2NF trivially satisfied). Transitive dependencies were eliminated: `company_name` and `industry` were moved to the `Companies` table (not stored in `Placement_Drives`), `city` and `state` to `Locations`, and `skill_name` to `Skills`.

#### 3.1.4 Relationship Modelling

Foreign keys were defined between all related tables:
- **ON DELETE CASCADE** was applied to weak-entity tables (`Application_Status_History`, `Selection_Rounds`, `Round_Results`, `Student_Skills`) so that deleting a parent automatically removes dependent records.
- Direct foreign key references (without CASCADE) were used where preserving data integrity requires manual cleanup (`Applications` → `Placement_Drives`).

#### 3.1.5 Constraint Design

Named constraints were used throughout (e.g., `uq_company_name`, `chk_cgpa`, `chk_phone`). CHECK constraints enforce business rules at the database layer: CGPA between 0.0 and 10.0, phone number exactly 10 digits, CTC > 0, year between 1 and 4, and backlogs ≥ 0. ENUM constraints restrict application status and round types to defined value sets.

#### 3.1.6 Trigger Design

Two triggers were designed: both are AFTER triggers on the `Applications` table. The first fires on INSERT to record the initial status. The second fires on UPDATE to record status changes. Both write to `Application_Status_History` — the Flask application never writes to this table directly.

#### 3.1.7 Stored Procedure Design

The stored procedure `sp_update_status` was designed to enforce the one-student-one-company placement policy. It accepts an application ID and a new status. When the status is 'Selected', it automatically withdraws all other active applications for that student. This keeps the business rule at the database level.

### 3.2 Application Architecture

The application follows a two-tier (client-server) architecture:

| Layer | Technology | Details |
|---|---|---|
| Presentation (UI) | Flask + Jinja2 + Bootstrap 5 | `login.html`, `register.html`, `dashboard.html`, `drives.html`, `officer_dashboard.html`, `post_drive.html`, `view_applicants.html`, etc. |
| Business Logic | Python (Flask routes) | `app.py` — route handlers with session management |
| Data Access | mysql-connector-python | `get_db()` connection helper, parameterised queries, `callproc()` for stored procedures |

### 3.3 Flask–Database Integration Methodology

Every user action in the Flask UI triggers a route handler in `app.py`. Route handlers obtain a MySQL connection from `get_db()`, execute queries using parameterised `cursor.execute()` (preventing SQL injection), process the results, and return rendered templates. The stored procedure is invoked via `cursor.callproc()`. Server-side validation replicates client-side checks as a second line of defence.

---

## CHAPTER 4: ER DIAGRAM & RELATIONAL TABLES WITH SAMPLE DATA

### 4.1 ER Diagram

*(Insert your ER diagram image here)*

Key design decisions reflected in the ER diagram:
1. Skills are modelled as a multi-valued attribute of Student, resolved into the `Student_Skills` junction table.
2. Each Company belongs to exactly one Location (Many-to-One).
3. Each Application links a Student to a Placement Drive (M:N resolved).
4. Selection Rounds belong to a Drive (One-to-Many), and Round Results link Rounds to Students (M:N resolved).

### 4.2 Table Catalogue with Sample Data

---

#### Table 1: Locations

Lookup table for company locations. Satisfies 3NF: city and state depend only on `location_id`.

**Relationships:** Locations → Companies (One-to-Many)

| Column | Type | Constraints | Description |
|---|---|---|---|
| location_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique location ID |
| city | VARCHAR(100) | NOT NULL, CHECK(≠blank) | City name |
| state | VARCHAR(100) | NOT NULL, CHECK(≠blank) | State name |
| country | VARCHAR(100) | NOT NULL, DEFAULT 'India' | Country name |

**Sample Data:**

| location_id | city | state | country |
|---|---|---|---|
| 1 | Bangalore | Karnataka | India |
| 2 | Hyderabad | Telangana | India |
| 3 | Mumbai | Maharashtra | India |
| 4 | Chennai | Tamil Nadu | India |
| 5 | Pune | Maharashtra | India |
| 6 | Noida | Uttar Pradesh | India |

---

#### Table 2: Companies

Stores company details linked to a location. UNIQUE constraint on `company_name` prevents duplicates.

**Relationships:** Companies → Placement_Drives (One-to-Many) | Companies → Locations (Many-to-One)

| Column | Type | Constraints | Description |
|---|---|---|---|
| company_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique company ID |
| company_name | VARCHAR(150) | NOT NULL, UNIQUE, CHECK(≠blank) | Company name |
| industry | VARCHAR(100) | NOT NULL | Industry sector |
| location_id | INT | NOT NULL, FK → Locations(location_id) | Company location |

**Sample Data:**

| company_id | company_name | industry | location_id |
|---|---|---|---|
| 1 | Google | Technology | 1 |
| 2 | Microsoft | Technology | 2 |
| 3 | Infosys | IT Services | 1 |
| 4 | Wipro | IT Services | 2 |
| 5 | Goldman Sachs | Finance | 3 |
| 6 | Amazon | E-Commerce | 1 |
| 7 | Deloitte | Consulting | 4 |
| 8 | Razorpay | Fintech | 1 |

---

#### Table 3: Placement_Officers

Stores TPO login credentials and department info.

**Relationships:** Placement_Officers → Placement_Drives (One-to-Many)

| Column | Type | Constraints | Description |
|---|---|---|---|
| officer_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique officer ID |
| name | VARCHAR(150) | NOT NULL, CHECK(≠blank) | Officer name |
| email | VARCHAR(150) | NOT NULL, UNIQUE, CHECK(email format) | Login email |
| password | VARCHAR(255) | NOT NULL, CHECK(≥6 chars) | Password |
| department | VARCHAR(100) | NOT NULL, DEFAULT 'Training & Placement' | Department |
| drive_id | INT | FK → Placement_Drives(drive_id) | Associated drive |

**Sample Data:**

| officer_id | name | email | department |
|---|---|---|---|
| 1 | Dr. Ramesh Kumar | ramesh@college.edu | Training & Placement |
| 2 | Ms. Sunita Rao | sunita@college.edu | Training & Placement |
| 3 | Mr. Anil Mehta | anil@college.edu | Training & Placement |

---

#### Table 4: Placement_Drives

Core drive entity linking a company to a role, with eligibility criteria.

**Relationships:** → Companies (Many-to-One) | → Placement_Officers (Many-to-One) | Placement_Drives → Applications (One-to-Many) | → Selection_Rounds (One-to-Many, CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| drive_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique drive ID |
| company_id | INT | NOT NULL, FK → Companies | Company offering the role |
| officer_id | INT | FK → Placement_Officers | TPO managing the drive |
| role | VARCHAR(200) | NOT NULL, CHECK(≠blank) | Job title |
| ctc | DECIMAL(10,2) | NOT NULL, CHECK(>0) | Annual CTC in ₹ |
| drive_date | DATE | NOT NULL | Scheduled drive date |
| eligibility_cgpa | DECIMAL(3,1) | NOT NULL, DEFAULT 6.0, CHECK(0–10) | Minimum CGPA required |
| eligible_branches | VARCHAR(255) | NOT NULL | Comma-separated eligible branches |

**Sample Data:**

| drive_id | company | role | ctc | drive_date | min_cgpa | branches |
|---|---|---|---|---|---|---|
| 1 | Google | Software Engineer | 24,00,000 | 2026-04-15 | 7.5 | CSE,ISE,AIML |
| 2 | Microsoft | SDE | 18,00,000 | 2026-04-20 | 7.0 | CSE,ISE,ECE |
| 3 | Infosys | Systems Engineer | 6,00,000 | 2026-04-25 | 6.5 | CSE,ISE,ECE,EEE |

---

#### Table 5: Students

Core student entity with personal and academic data.

**Relationships:** Students → Applications (One-to-Many) | Students ↔ Skills via Student_Skills (M:N)

| Column | Type | Constraints | Description |
|---|---|---|---|
| student_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique student ID |
| name | VARCHAR(150) | NOT NULL, CHECK(≠blank) | Full name |
| email | VARCHAR(150) | NOT NULL, UNIQUE, CHECK(email format) | Login email |
| password | VARCHAR(255) | NOT NULL, CHECK(≥6 chars) | Password |
| phone | VARCHAR(10) | NOT NULL, CHECK(10 digits regex) | Phone number |
| branch | VARCHAR(100) | NOT NULL | Academic branch |
| year | INT | NOT NULL, CHECK(1–4) | Current year |
| cgpa | DECIMAL(3,1) | NOT NULL, CHECK(0.0–10.0) | Current CGPA |
| backlogs | INT | NOT NULL, DEFAULT 0, CHECK(≥0) | Active backlogs |
| city | VARCHAR(100) | | Hometown city |
| state | VARCHAR(100) | | Hometown state |

**Sample Data:**

| student_id | name | email | branch | year | cgpa |
|---|---|---|---|---|---|
| 1 | Akash Kumar | akash@student.com | CSE | 4 | 8.5 |
| 2 | Divya Patel | divya@student.com | ECE | 4 | 7.8 |
| 3 | Rohan Singh | rohan@student.com | ISE | 4 | 9.1 |

---

#### Table 6: Applications ⭐ (Main Table)

Links students to drives. Composite UNIQUE constraint prevents duplicate applications.

**Relationships:** → Students (Many-to-One) | → Placement_Drives (Many-to-One) | Applications → Application_Status_History (One-to-Many, CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| application_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique application ID |
| student_id | INT | NOT NULL, FK → Students | Applicant |
| drive_id | INT | NOT NULL, FK → Placement_Drives | Target drive |
| applied_date | DATE | NOT NULL, DEFAULT CURRENT_DATE | Date of application |
| status | ENUM | NOT NULL, DEFAULT 'Applied' | Applied / Shortlisted / In Process / Selected / Rejected / Withdrawn |

**Constraint:** `UNIQUE (student_id, drive_id)` — one student cannot apply to the same drive twice.

---

#### Table 7: Application_Status_History

Audit trail written exclusively by database triggers. Flask code never writes to this table.

**Relationships:** → Applications (Many-to-One, ON DELETE CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| history_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique log entry ID |
| application_id | INT | NOT NULL, FK → Applications ON CASCADE | Parent application |
| status | VARCHAR(50) | NOT NULL | Status value at time of change |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When the change occurred |

---

#### Table 8: Selection_Rounds

Stores selection rounds per drive. ON DELETE CASCADE from Placement_Drives.

**Relationships:** → Placement_Drives (Many-to-One, CASCADE) | Selection_Rounds → Round_Results (One-to-Many, CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| round_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique round ID |
| drive_id | INT | NOT NULL, FK → Placement_Drives ON CASCADE | Parent drive |
| round_name | VARCHAR(150) | NOT NULL, CHECK(≠blank) | Round name |
| round_type | ENUM | NOT NULL, DEFAULT 'Technical' | Aptitude / Technical / HR / Group Discussion / Case Study |
| round_date | DATE | NOT NULL | Scheduled date |

---

#### Table 9: Round_Results

Per-student results for each round. Composite UNIQUE prevents duplicate results.

**Relationships:** → Selection_Rounds (Many-to-One, CASCADE) | → Students (Many-to-One)

| Column | Type | Constraints | Description |
|---|---|---|---|
| result_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique result ID |
| round_id | INT | NOT NULL, FK → Selection_Rounds ON CASCADE | Parent round |
| student_id | INT | NOT NULL, FK → Students | Student evaluated |
| result | ENUM | NOT NULL, DEFAULT 'Pending' | Pending / Pass / Fail |
| remarks | VARCHAR(500) | | Evaluator notes |

**Constraint:** `UNIQUE (round_id, student_id)` — one result per student per round.

---

#### Table 10: Skills

Master lookup for skills. Separating `skill_name` from students satisfies 1NF.

**Relationships:** Skills ↔ Students via Student_Skills (M:N, CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| skill_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique skill ID |
| skill_name | VARCHAR(100) | NOT NULL, UNIQUE, CHECK(≠blank) | Skill name |

**Sample Data:** Python, Java, SQL, Machine Learning, React, Data Structures, System Design, C++, Cloud Computing, Communication

---

#### Table 11: Student_Skills (Junction Table)

Resolves the M:N between Students and Skills. Composite PK ensures no duplicate skill per student.

**Relationships:** → Students (ON DELETE CASCADE) | → Skills (ON DELETE CASCADE)

| Column | Type | Constraints | Description |
|---|---|---|---|
| student_id | INT | NOT NULL, FK → Students ON CASCADE | Student |
| skill_id | INT | NOT NULL, FK → Skills ON CASCADE | Skill |

**Primary Key:** `(student_id, skill_id)`

---

## CHAPTER 5: DDL COMMANDS & PL/SQL PROCEDURES / TRIGGERS

### 5.1 DDL Commands

#### 5.1.1 Database Creation

```sql
CREATE DATABASE IF NOT EXISTS placement_db;
USE placement_db;
```

#### 5.1.2 Key Table DDL Samples

The following representative CREATE TABLE statements illustrate the constraint design. Full DDL is in `schema.sql`.

**Students table:**
```sql
CREATE TABLE Students (
    student_id    INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    email         VARCHAR(150) NOT NULL,
    password      VARCHAR(255) NOT NULL,
    phone         VARCHAR(10)  NOT NULL,
    branch        VARCHAR(100) NOT NULL,
    year          INT          NOT NULL,
    cgpa          DECIMAL(3,1) NOT NULL,
    backlogs      INT          NOT NULL DEFAULT 0,
    city          VARCHAR(100),
    state         VARCHAR(100),

    CONSTRAINT uq_student_email    UNIQUE (email),
    CONSTRAINT chk_student_email   CHECK (email LIKE '%@%.%'),
    CONSTRAINT chk_phone           CHECK (phone REGEXP '^[0-9]{10}$'),
    CONSTRAINT chk_cgpa            CHECK (cgpa >= 0.0 AND cgpa <= 10.0),
    CONSTRAINT chk_year            CHECK (year BETWEEN 1 AND 4),
    CONSTRAINT chk_backlogs        CHECK (backlogs >= 0),
    CONSTRAINT chk_student_pwd     CHECK (CHAR_LENGTH(password) >= 6),
    CONSTRAINT chk_student_name    CHECK (CHAR_LENGTH(TRIM(name)) > 0)
);
```

**Applications table (with ENUM):**
```sql
CREATE TABLE Applications (
    application_id  INT  AUTO_INCREMENT PRIMARY KEY,
    student_id      INT  NOT NULL,
    drive_id        INT  NOT NULL,
    applied_date    DATE NOT NULL DEFAULT (CURRENT_DATE),
    status          ENUM('Applied','Shortlisted','In Process','Selected',
                         'Rejected','Withdrawn') NOT NULL DEFAULT 'Applied',

    CONSTRAINT uq_application UNIQUE (student_id, drive_id),

    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (drive_id)   REFERENCES Placement_Drives(drive_id)
);
```

**Student_Skills junction table:**
```sql
CREATE TABLE Student_Skills (
    student_id  INT NOT NULL,
    skill_id    INT NOT NULL,
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id)   REFERENCES Skills(skill_id) ON DELETE CASCADE
);
```

### 5.2 Views

Two views are defined in the database. They encapsulate complex multi-table JOINs for reuse by the Flask application.

#### View 1: vw_drive_listing

| Property | Value |
|---|---|
| Purpose | Full drive listing joining Drives + Companies + Locations |
| Tables Joined | Placement_Drives, Companies, Locations |
| Used By | `drives()` route — public drives listing page |

```sql
CREATE VIEW vw_drive_listing AS
SELECT d.drive_id, d.role, c.company_name, c.industry,
       l.city, l.state, d.ctc, d.drive_date,
       d.eligibility_cgpa, d.eligible_branches
FROM Placement_Drives d
JOIN Companies c ON d.company_id  = c.company_id
JOIN Locations l ON c.location_id = l.location_id;
```

#### View 2: vw_application_details

| Property | Value |
|---|---|
| Purpose | Full application details joining 4 tables |
| Tables Joined | Applications, Students, Placement_Drives, Companies |
| Used By | Application detail and reporting queries |

```sql
CREATE VIEW vw_application_details AS
SELECT a.application_id, s.name AS student_name, s.email AS student_email,
       s.branch, s.cgpa, d.role, c.company_name, a.applied_date, a.status
FROM Applications a
JOIN Students         s ON a.student_id = s.student_id
JOIN Placement_Drives d ON a.drive_id   = d.drive_id
JOIN Companies        c ON d.company_id = c.company_id;
```

### 5.3 Triggers

Two triggers automate the application status audit trail. Both are row-level triggers (FOR EACH ROW).

#### Trigger 1: after_application_insert

| Property | Value |
|---|---|
| Event | AFTER INSERT |
| Table | Applications |
| Purpose | Auto-records the initial "Applied" status in the history table when a new application is created |

```sql
CREATE TRIGGER after_application_insert
AFTER INSERT ON Applications
FOR EACH ROW
BEGIN
    INSERT INTO Application_Status_History(application_id, status, updated_at)
    VALUES (NEW.application_id, NEW.status, NOW());
END;
```

**Explanation:** Fires automatically when a student applies to a drive. The Flask `apply()` route never writes to `Application_Status_History` — the trigger handles it entirely. This ensures every application has a complete status trail from creation.

#### Trigger 2: after_application_update

| Property | Value |
|---|---|
| Event | AFTER UPDATE |
| Table | Applications |
| Purpose | Records a new history entry whenever the application status changes. The IF condition prevents duplicate entries when non-status columns are updated. |

```sql
CREATE TRIGGER after_application_update
AFTER UPDATE ON Applications
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO Application_Status_History(application_id, status, updated_at)
        VALUES (NEW.application_id, NEW.status, NOW());
    END IF;
END;
```

**Explanation:** The `IF OLD.status <> NEW.status` condition prevents unnecessary audit rows when other columns are updated without a status change. Fires both when the TPO manually changes status and when the stored procedure auto-withdraws applications.

### 5.4 Stored Procedure

#### Procedure: sp_update_status (Placement Policy Enforcement)

| Parameter | Direction | Data Type | Description |
|---|---|---|---|
| p_application_id | IN | INT | Application to update |
| p_new_status | IN | VARCHAR(50) | New status value |

```sql
CREATE PROCEDURE sp_update_status(
    IN p_application_id INT,
    IN p_new_status VARCHAR(50)
)
BEGIN
    -- Step 1: Update the target application's status
    UPDATE Applications
    SET status = p_new_status
    WHERE application_id = p_application_id;

    -- Step 2: If selected, withdraw all other active applications
    IF p_new_status = 'Selected' THEN
        UPDATE Applications
        SET status = 'Withdrawn'
        WHERE student_id = (
            SELECT student_id FROM (
                SELECT student_id FROM Applications
                WHERE application_id = p_application_id
            ) AS tmp
        )
        AND application_id <> p_application_id
        AND status NOT IN ('Rejected', 'Withdrawn');
    END IF;
END;
```

**Explanation:** This stored procedure enforces the college's one-student-one-company placement policy entirely at the database level. When the TPO marks a student as "Selected" for one company, the procedure automatically sets all their other active applications to "Withdrawn". The subquery pattern `SELECT ... FROM (SELECT ...) AS tmp` is used to work around MySQL's limitation of not allowing a table being updated to be directly referenced in a subquery.

**Flask invocation:**
```python
cur.callproc("sp_update_status", (app_id, request.form["status"]))
```

---

## CHAPTER 6: RESULTS & SNAPSHOTS

*(Insert screenshots for each section below)*

### 6.1 Home Page
The landing page showing aggregate statistics: total drives, registered students, students placed, and companies participating. Features animated counters and a modern glassmorphism card design.

### 6.2 Student Registration
Registration form with real-time client-side validation (name, email, password strength meter, phone digit restriction, CGPA range). Includes toggleable skill chips for selecting skills during registration.

### 6.3 Student Login
Clean login form with email/password fields and flash message support for success/error notifications.

### 6.4 Student Dashboard
Post-login dashboard showing stats cards: Total Applications, Selected, Shortlisted, In Process. Below shows recent applications table with status badges.

### 6.5 Student Profile
Profile page displaying student details, skill badges, and application statistics.

### 6.6 Drives Listing
Public listing of all placement drives with company name, role, CTC, drive date, eligible branches (pill badges), and applicant count. "Apply Now" button shown only for eligible students.

### 6.7 Application Detail
Detailed view of a single application showing status timeline (history from triggers), selection round results, and current status.

### 6.8 TPO Login
Officer login page with email/password authentication.

### 6.9 TPO Dashboard
Officer dashboard with stats: Total Drives, Applications, Students Placed, Active Students. Below shows a table of all drives with Manage and Delete buttons.

### 6.10 Post Drive
Drive creation form with company dropdown (with "Add New Company" collapsible section), role, CTC, date, CGPA cutoff, and branch selector chips. Company management section with delete capability.

### 6.11 View Applicants
Per-drive applicant management showing student details, status dropdown for updates, selection rounds, and round-wise result management.

### 6.12 Auto-Withdrawal Demo
Screenshot showing: (1) Student with multiple applications, (2) TPO marks one as "Selected", (3) All other applications automatically change to "Withdrawn" — demonstrating the stored procedure in action.

---

## CHAPTER 7: CONCLUSION, LIMITATIONS & FUTURE WORK

### 7.1 Conclusion

This project successfully demonstrates the design and implementation of a complete Placement Management System using a two-tier Flask and MySQL architecture. The system fulfils all stated objectives:

1. An **eleven-table relational database schema** normalised to Third Normal Form (3NF) was designed and implemented. Multi-valued dependencies were resolved through proper table decomposition — skills into `Student_Skills` junction table.
2. **Two database triggers** automate the complete application status audit trail (`Application_Status_History`) entirely at the database level, independent of application code.
3. **One stored procedure** (`sp_update_status`) enforces the one-student-one-company placement policy at the database level. When a student is marked "Selected", all other applications are automatically withdrawn.
4. **Two database views** (`vw_drive_listing`, `vw_application_details`) encapsulate complex multi-table JOINs for reuse by the Flask application.
5. A **Flask web application** connects to MySQL via `mysql-connector-python`, using parameterised queries for all database access and `callproc()` for stored procedure invocation.
6. **Role-based access control** is enforced at the application level: Students see dashboards and apply to drives; TPO Officers manage drives, companies, applicants, and selection rounds.

The project demonstrates that placing business logic at the correct architectural layer — validation at the UI, route-level access control in Flask, and data integrity rules at the database — produces a system that is more reliable and consistent than one where all logic lives in application code alone.

### 7.2 Current Limitations

**Security:**
- Passwords are stored as plain text in the database. A production deployment must use a hashing algorithm such as bcrypt.
- There is no session timeout beyond Flask's default cookie expiry.
- The MySQL connection uses default credentials without SSL — acceptable only in a development environment.

**Data Model:**
- Eligible branches are stored as a comma-separated string rather than a normalised junction table. This makes branch-based queries less efficient.
- The ENUM for application status requires schema changes to add new status values.

**UI/UX:**
- No loading indicators during database queries.
- No pagination for large drive or applicant lists.

### 7.3 Future Enhancements

1. **Password hashing**: Integrate `bcrypt` library to hash passwords on storage and use `bcrypt.checkpw()` during authentication.
2. **Resume upload**: Add a file upload field for students to attach PDF resumes, stored with file paths in the database.
3. **Email notifications**: Send automated emails to students when their application status changes using Flask-Mail.
4. **Analytics dashboard**: Add charts (using Chart.js) for branch-wise placement statistics, company-wise CTC distribution, and year-over-year trends.
5. **Eligible branches normalisation**: Replace the comma-separated `eligible_branches` column with a proper junction table for better query performance.
6. **Cloud deployment**: Deploy on AWS/GCP with MySQL RDS for remote access and automated backups.

---

## CHAPTER 8: REFERENCES

[1] Silberschatz, A., Korth, H. F., and Sudarshan, S. (2019). *Database System Concepts*, 7th Edition. McGraw-Hill Education.

[2] Ramakrishnan, R. and Gehrke, J. (2003). *Database Management Systems*, 3rd Edition. McGraw-Hill.

[3] Oracle Corporation. MySQL 8.0 Reference Manual — CREATE TABLE, CREATE TRIGGER, CREATE PROCEDURE. Available at: https://dev.mysql.com/doc/refman/8.0/en/

[4] Oracle Corporation. MySQL 8.0 Reference Manual — Stored Routines. Available at: https://dev.mysql.com/doc/refman/8.0/en/stored-routines.html

[5] Oracle Corporation. MySQL 8.0 Reference Manual — Using Triggers. Available at: https://dev.mysql.com/doc/refman/8.0/en/triggers.html

[6] Pallets Projects. Flask Documentation. Available at: https://flask.palletsprojects.com/

[7] MySQL Connector/Python Developer Guide. Available at: https://dev.mysql.com/doc/connector-python/en/

[8] Bootstrap 5 Documentation. Available at: https://getbootstrap.com/docs/5.3/

[9] Codd, E. F. (1970). A Relational Model of Data for Large Shared Data Banks. *Communications of the ACM*, 13(6), 377–387.

[10] Date, C. J. (2003). *An Introduction to Database Systems*, 8th Edition. Addison-Wesley.

[11] MIT Manipal. (2025). CSS 2212 — Database Systems Lab Manual. School of Computer Engineering, Manipal Institute of Technology.
