-- ============================================================
--  PLACEMENT MANAGEMENT SYSTEM — Complete SQL Schema
--  CSS 2212 - DBS Lab Mini Project
--
--  CONSTRAINTS USED:
--  • PRIMARY KEY         — unique identifier per table
--  • FOREIGN KEY         — referential integrity between tables
--  • NOT NULL            — mandatory fields
--  • UNIQUE              — no duplicate emails, skill names, company names
--  • DEFAULT             — sensible default values
--  • CHECK               — domain integrity (CGPA, phone, year, CTC etc.)
--  • ON DELETE CASCADE   — auto-remove child rows when parent is deleted
-- ============================================================

CREATE DATABASE IF NOT EXISTS placement_db;
USE placement_db;

-- ─────────────────────────────────────────────
-- TABLE 1: Locations
-- ─────────────────────────────────────────────
CREATE TABLE Locations (
    location_id   INT AUTO_INCREMENT PRIMARY KEY,
    city          VARCHAR(100) NOT NULL,
    state         VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL DEFAULT 'India',

    CONSTRAINT chk_city  CHECK (CHAR_LENGTH(TRIM(city))  > 0),
    CONSTRAINT chk_state CHECK (CHAR_LENGTH(TRIM(state)) > 0)
);

-- ─────────────────────────────────────────────
-- TABLE 2: Companies
-- ─────────────────────────────────────────────
CREATE TABLE Companies (
    company_id    INT AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(150) NOT NULL,
    industry      VARCHAR(100) NOT NULL,
    location_id   INT NOT NULL,

    CONSTRAINT uq_company_name  UNIQUE (company_name),
    CONSTRAINT chk_company_name CHECK (CHAR_LENGTH(TRIM(company_name)) > 0),

    FOREIGN KEY (location_id) REFERENCES Locations(location_id)
);

-- ─────────────────────────────────────────────
-- TABLE 3: Placement_Officers
-- ─────────────────────────────────────────────
CREATE TABLE Placement_Officers (
    officer_id    INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    email         VARCHAR(150) NOT NULL,
    password      VARCHAR(255) NOT NULL,
    department    VARCHAR(100) NOT NULL DEFAULT 'Training & Placement',
    drive_id      INT,

    CONSTRAINT uq_officer_email    UNIQUE (email),
    CONSTRAINT chk_officer_email   CHECK (email LIKE '%@%.%'),
    CONSTRAINT chk_officer_pwd     CHECK (CHAR_LENGTH(password) >= 6),
    CONSTRAINT chk_officer_name    CHECK (CHAR_LENGTH(TRIM(name)) > 0)
);

-- ─────────────────────────────────────────────
-- TABLE 4: Placement_Drives
-- ─────────────────────────────────────────────
CREATE TABLE Placement_Drives (
    drive_id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id         INT          NOT NULL,
    officer_id         INT,
    role               VARCHAR(200) NOT NULL,
    ctc                DECIMAL(10,2) NOT NULL,
    drive_date         DATE          NOT NULL,
    eligibility_cgpa   DECIMAL(3,1)  NOT NULL DEFAULT 6.0,
    eligible_branches  VARCHAR(255)  NOT NULL,

    CONSTRAINT chk_ctc              CHECK (ctc > 0),
    CONSTRAINT chk_eligibility_cgpa CHECK (eligibility_cgpa >= 0.0 AND eligibility_cgpa <= 10.0),
    CONSTRAINT chk_role             CHECK (CHAR_LENGTH(TRIM(role)) > 0),

    FOREIGN KEY (company_id) REFERENCES Companies(company_id),
    FOREIGN KEY (officer_id) REFERENCES Placement_Officers(officer_id)
);

-- FK back from Officers → Drives (after Drives table exists)
ALTER TABLE Placement_Officers
ADD CONSTRAINT fk_officer_drive
FOREIGN KEY (drive_id) REFERENCES Placement_Drives(drive_id);

-- ─────────────────────────────────────────────
-- TABLE 5: Students
-- ─────────────────────────────────────────────
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

-- ─────────────────────────────────────────────
-- TABLE 6: Applications  ⭐ MAIN TABLE
-- ─────────────────────────────────────────────
CREATE TABLE Applications (
    application_id  INT  AUTO_INCREMENT PRIMARY KEY,
    student_id      INT  NOT NULL,
    drive_id        INT  NOT NULL,
    applied_date    DATE NOT NULL DEFAULT (CURRENT_DATE),
    status          ENUM('Applied','Shortlisted','In Process','Selected','Rejected','Withdrawn')
                    NOT NULL DEFAULT 'Applied',

    -- one student cannot apply to the same drive twice
    CONSTRAINT uq_application UNIQUE (student_id, drive_id),

    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (drive_id)   REFERENCES Placement_Drives(drive_id)
);

-- ─────────────────────────────────────────────
-- TABLE 7: Application_Status_History
-- ─────────────────────────────────────────────
CREATE TABLE Application_Status_History (
    history_id      INT      AUTO_INCREMENT PRIMARY KEY,
    application_id  INT      NOT NULL,
    status          VARCHAR(50) NOT NULL,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (application_id)
        REFERENCES Applications(application_id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- TABLE 8: Selection_Rounds
-- ─────────────────────────────────────────────
CREATE TABLE Selection_Rounds (
    round_id    INT AUTO_INCREMENT PRIMARY KEY,
    drive_id    INT          NOT NULL,
    round_name  VARCHAR(150) NOT NULL,
    round_type  ENUM('Aptitude','Technical','HR','Group Discussion','Case Study')
                NOT NULL DEFAULT 'Technical',
    round_date  DATE NOT NULL,

    CONSTRAINT chk_round_name CHECK (CHAR_LENGTH(TRIM(round_name)) > 0),

    FOREIGN KEY (drive_id)
        REFERENCES Placement_Drives(drive_id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- TABLE 9: Round_Results
-- ─────────────────────────────────────────────
CREATE TABLE Round_Results (
    result_id   INT AUTO_INCREMENT PRIMARY KEY,
    round_id    INT NOT NULL,
    student_id  INT NOT NULL,
    result      ENUM('Pending','Pass','Fail') NOT NULL DEFAULT 'Pending',
    remarks     VARCHAR(500),

    -- one result per student per round
    CONSTRAINT uq_round_result UNIQUE (round_id, student_id),

    FOREIGN KEY (round_id)
        REFERENCES Selection_Rounds(round_id)
        ON DELETE CASCADE,
    FOREIGN KEY (student_id)
        REFERENCES Students(student_id)
);

-- ─────────────────────────────────────────────
-- TABLE 10: Skills
-- ─────────────────────────────────────────────
CREATE TABLE Skills (
    skill_id    INT AUTO_INCREMENT PRIMARY KEY,
    skill_name  VARCHAR(100) NOT NULL,

    CONSTRAINT uq_skill_name  UNIQUE (skill_name),
    CONSTRAINT chk_skill_name CHECK (CHAR_LENGTH(TRIM(skill_name)) > 0)
);

-- ─────────────────────────────────────────────
-- TABLE 11: Student_Skills  (Junction Table)
-- ─────────────────────────────────────────────
CREATE TABLE Student_Skills (
    student_id  INT NOT NULL,
    skill_id    INT NOT NULL,

    -- composite PK ensures no duplicate skill per student
    PRIMARY KEY (student_id, skill_id),

    FOREIGN KEY (student_id)
        REFERENCES Students(student_id)
        ON DELETE CASCADE,
    FOREIGN KEY (skill_id)
        REFERENCES Skills(skill_id)
        ON DELETE CASCADE
);

-- ============================================================
--  TRIGGERS
-- ============================================================

DELIMITER $$

-- TRIGGER 1: Auto-insert status history when application is created
CREATE TRIGGER after_application_insert
AFTER INSERT ON Applications
FOR EACH ROW
BEGIN
    INSERT INTO Application_Status_History(application_id, status, updated_at)
    VALUES (NEW.application_id, NEW.status, NOW());
END$$

-- TRIGGER 2: Auto-insert status history when status is updated
CREATE TRIGGER after_application_update
AFTER UPDATE ON Applications
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO Application_Status_History(application_id, status, updated_at)
        VALUES (NEW.application_id, NEW.status, NOW());
    END IF;
END$$

-- STORED PROCEDURE: Update status & auto-withdraw others on selection
CREATE PROCEDURE sp_update_status(
    IN p_application_id INT,
    IN p_new_status VARCHAR(50)
)
BEGIN
    -- Step 1: Update the target application's status
    UPDATE Applications
    SET status = p_new_status
    WHERE application_id = p_application_id;

    -- Step 2: If selected, withdraw all other active applications for that student
    IF p_new_status = 'Selected' THEN
        UPDATE Applications
        SET status = 'Withdrawn'
        WHERE student_id = (SELECT student_id FROM (SELECT student_id FROM Applications WHERE application_id = p_application_id) AS tmp)
          AND application_id <> p_application_id
          AND status NOT IN ('Rejected', 'Withdrawn');
    END IF;
END$$

DELIMITER ;

-- ============================================================
--  VIEWS
-- ============================================================

-- VIEW 1: Full drive listing joining Drives + Companies + Locations
CREATE VIEW vw_drive_listing AS
SELECT
    d.drive_id,
    d.role,
    c.company_name,
    c.industry,
    l.city,
    l.state,
    d.ctc,
    d.drive_date,
    d.eligibility_cgpa,
    d.eligible_branches
FROM Placement_Drives d
JOIN Companies c ON d.company_id  = c.company_id
JOIN Locations l ON c.location_id = l.location_id;

-- VIEW 2: Full application details joining 4 tables
CREATE VIEW vw_application_details AS
SELECT
    a.application_id,
    s.name         AS student_name,
    s.email        AS student_email,
    s.branch,
    s.cgpa,
    d.role,
    c.company_name,
    a.applied_date,
    a.status
FROM Applications a
JOIN Students         s ON a.student_id = s.student_id
JOIN Placement_Drives d ON a.drive_id   = d.drive_id
JOIN Companies        c ON d.company_id = c.company_id;

-- ============================================================
--  SAMPLE DATA
-- ============================================================

INSERT INTO Locations (city, state, country) VALUES
('Bangalore',  'Karnataka',    'India'),
('Hyderabad',  'Telangana',    'India'),
('Mumbai',     'Maharashtra',  'India'),
('Chennai',    'Tamil Nadu',   'India'),
('Pune',       'Maharashtra',  'India'),
('Noida',      'Uttar Pradesh','India');

INSERT INTO Companies (company_name, industry, location_id) VALUES
('Google',        'Technology',  1),
('Microsoft',     'Technology',  2),
('Infosys',       'IT Services', 1),
('Wipro',         'IT Services', 2),
('Goldman Sachs', 'Finance',     3),
('Amazon',        'E-Commerce',  1),
('Deloitte',      'Consulting',  4),
('Razorpay',      'Fintech',     1);

INSERT INTO Placement_Officers (name, email, password, department) VALUES
('Dr. Ramesh Kumar', 'ramesh@college.edu', 'tpo123456', 'Training & Placement'),
('Ms. Sunita Rao',   'sunita@college.edu', 'tpo123456', 'Training & Placement'),
('Mr. Anil Mehta',   'anil@college.edu',   'tpo123456', 'Training & Placement');

INSERT INTO Students
(name, email, password, phone, branch, year, cgpa, backlogs, city, state) VALUES
('Akash Kumar', 'akash@student.com', 'student123', '9876543210', 'CSE',  4, 8.5, 0, 'Udupi',     'Karnataka'),
('Divya Patel', 'divya@student.com', 'student123', '9845012345', 'ECE',  4, 7.8, 0, 'Mangalore', 'Karnataka'),
('Rohan Singh', 'rohan@student.com', 'student123', '9731234567', 'ISE',  4, 9.1, 0, 'Mysore',    'Karnataka'),
('Sneha Menon', 'sneha@student.com', 'student123', '8867452310', 'CSE',  4, 8.9, 0, 'Hubli',     'Karnataka'),
('Arjun Verma', 'arjun@student.com', 'student123', '7760123456', 'AIML', 4, 7.2, 1, 'Belgaum',   'Karnataka'),
('Priya Nair',  'priya@student.com', 'student123', '9900112233', 'CSE',  4, 9.4, 0, 'Udupi',     'Karnataka');

INSERT INTO Placement_Drives
(company_id, officer_id, role, ctc, drive_date, eligibility_cgpa, eligible_branches) VALUES
(1, 1, 'Software Engineer',             2400000, '2026-04-15', 7.5, 'CSE,ISE,AIML'),
(2, 1, 'Software Development Engineer', 1800000, '2026-04-20', 7.0, 'CSE,ISE,ECE'),
(3, 2, 'Systems Engineer',               600000, '2026-04-25', 6.5, 'CSE,ISE,ECE,EEE'),
(4, 2, 'Project Engineer',               700000, '2026-05-01', 6.5, 'CSE,ISE,ECE'),
(5, 3, 'Analyst',                       1200000, '2026-05-05', 8.0, 'CSE,ISE'),
(6, 3, 'SDE-1',                         2000000, '2026-05-10', 7.5, 'CSE,ISE,AIML'),
(7, 1, 'Business Analyst',               900000, '2026-05-15', 7.0, 'CSE,ISE,ECE'),
(8, 2, 'Backend Engineer',              1500000, '2026-05-20', 7.5, 'CSE,ISE');

INSERT INTO Skills (skill_name) VALUES
('Python'), ('Java'), ('SQL'), ('Machine Learning'), ('React'),
('Data Structures'), ('System Design'), ('C++'), ('Cloud Computing'), ('Communication');

INSERT INTO Student_Skills VALUES
(1,1),(1,3),(1,6),(1,7),
(2,5),(2,1),(2,10),
(3,2),(3,3),(3,6),(3,7),
(4,1),(4,4),(4,6),
(5,1),(5,4),(5,9),
(6,1),(6,2),(6,6),(6,7),(6,3);

INSERT INTO Applications (student_id, drive_id, applied_date, status) VALUES
(1, 1, '2026-03-10', 'Shortlisted'),
(1, 2, '2026-03-11', 'Applied'),
(2, 3, '2026-03-12', 'In Process'),
(3, 1, '2026-03-10', 'Selected'),
(4, 5, '2026-03-13', 'Shortlisted'),
(5, 3, '2026-03-12', 'Rejected'),
(6, 1, '2026-03-10', 'In Process'),
(6, 6, '2026-03-14', 'Applied');

INSERT INTO Selection_Rounds (drive_id, round_name, round_type, round_date) VALUES
(1, 'Online Assessment',  'Aptitude',   '2026-03-20'),
(1, 'Technical Round 1',  'Technical',  '2026-03-25'),
(1, 'Technical Round 2',  'Technical',  '2026-03-28'),
(1, 'HR Round',           'HR',         '2026-04-02'),
(2, 'Coding Test',        'Technical',  '2026-03-22'),
(2, 'System Design',      'Technical',  '2026-03-27'),
(5, 'Aptitude Test',      'Aptitude',   '2026-03-18'),
(5, 'Case Study Round',   'Case Study', '2026-03-24');

INSERT INTO Round_Results (round_id, student_id, result, remarks) VALUES
(1, 1, 'Pass',    'Score: 87/100'),
(1, 3, 'Pass',    'Score: 94/100'),
(1, 6, 'Pass',    'Score: 91/100'),
(2, 1, 'Pass',    'Good knowledge of DSA'),
(2, 3, 'Pass',    'Excellent problem solving'),
(2, 6, 'Pending', 'Interview scheduled'),
(3, 3, 'Pass',    'Strong system design'),
(4, 3, 'Pass',    'Great cultural fit — offer extended'),
(7, 4, 'Pass',    'Score: 78/100'),
(8, 4, 'Pending', 'Case study under review');
