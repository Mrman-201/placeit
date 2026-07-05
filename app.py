"""
PLACEMENT MANAGEMENT SYSTEM — Flask Backend
CSS 2212 - DBS Lab Mini Project

Install: pip install flask mysql-connector-python
Run:     python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import date
from dotenv import load_dotenv

load_dotenv()  # Load .env variables (e.g. GROQ_API_KEY)

app = Flask(__name__)
app.secret_key = "placement_secret_2026"
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB upload limit

# Register AI Mentor blueprint
from ai_mentor import ai_mentor_bp
app.register_blueprint(ai_mentor_bp)

import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ── HOME ────────────────────────────────────────
@app.route("/")
def home():
    # Redirect logged-in users to their dashboard
    if session.get("role") == "student":
        return redirect(url_for("dashboard"))
    if session.get("role") == "officer":
        return redirect(url_for("officer_dashboard"))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as cnt FROM Placement_Drives")
    drives = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM Students")
    students = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM Applications WHERE status='Selected'")
    placed = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM Companies")
    companies = cur.fetchone()["cnt"]
    cur.close(); db.close()
    return render_template("home.html", drives=drives, students=students,
                           placed=placed, companies=companies)


# ── STUDENT AUTH ─────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        d = request.form
        # ── Server-side validation ──
        import re
        errors = []
        if not d.get("name", "").strip():
            errors.append("Name is required.")
        elif not re.match(r'^[A-Za-z\s]{2,}$', d["name"]):
            errors.append("Name must contain only letters and spaces (min 2 chars).")
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', d.get("email", "")):
            errors.append("Enter a valid email address.")
        if len(d.get("password", "")) < 6:
            errors.append("Password must be at least 6 characters.")
        if not re.match(r'^\d{10}$', d.get("phone", "")):
            errors.append("Phone number must be exactly 10 digits.")
        try:
            cgpa = float(d.get("cgpa", 0))
            if cgpa < 0 or cgpa > 10:
                errors.append("CGPA must be between 0.0 and 10.0.")
        except ValueError:
            errors.append("CGPA must be a valid number.")
        if not d.get("branch"):
            errors.append("Branch is required.")
        if not d.get("year"):
            errors.append("Year is required.")
        if errors:
            for e in errors:
                flash(e, "danger")
            db = get_db(); cur = db.cursor(dictionary=True)
            cur.execute("SELECT skill_id, skill_name FROM Skills ORDER BY skill_name")
            skills = cur.fetchall()
            cur.close(); db.close()
            return render_template("register.html", skills=skills)
        # ── Insert into DB ──
        db = get_db(); cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO Students (name,email,password,phone,branch,year,cgpa,backlogs,city,state)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (d["name"],d["email"],d["password"],d["phone"],d["branch"],
                  d["year"],d["cgpa"],d["backlogs"],d["city"],d["state"]))
            db.commit()
            student_id = cur.lastrowid
            # ── Insert selected skills ──
            selected_skills = request.form.getlist("skills")
            for skill_id in selected_skills:
                cur.execute("INSERT INTO Student_Skills (student_id, skill_id) VALUES (%s, %s)",
                            (student_id, int(skill_id)))
            db.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Email already registered.", "danger")
        finally:
            cur.close(); db.close()
    # GET: fetch available skills for the form
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT skill_id, skill_name FROM Skills ORDER BY skill_name")
    skills = cur.fetchall()
    cur.close(); db.close()
    return render_template("register.html", skills=skills)


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM Students WHERE email=%s AND password=%s",
                    (request.form["email"], request.form["password"]))
        student = cur.fetchone()
        cur.close(); db.close()
        if student:
            session["student_id"]   = student["student_id"]
            session["student_name"] = student["name"]
            session["cgpa"]         = float(student["cgpa"])
            session["branch"]       = student["branch"]
            session["role"]         = "student"
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ── STUDENT PROFILE ──────────────────────────────
@app.route("/profile")
def profile():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    sid = session["student_id"]
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM Students WHERE student_id=%s", (sid,))
    student = cur.fetchone()
    cur.execute("""
        SELECT sk.skill_name
        FROM Student_Skills ss
        JOIN Skills sk ON ss.skill_id = sk.skill_id
        WHERE ss.student_id=%s ORDER BY sk.skill_name
    """, (sid,))
    skills = [r["skill_name"] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s", (sid,))
    total_apps = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s AND status='Selected'", (sid,))
    selected = cur.fetchone()["c"]
    cur.close(); db.close()
    return render_template("profile.html", student=student, skills=skills,
                           total_apps=total_apps, selected=selected)


# ── STUDENT DASHBOARD ────────────────────────────
@app.route("/dashboard")
def dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    sid = session["student_id"]
    db = get_db(); cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s", (sid,))
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s AND status='Selected'", (sid,))
    selected = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s AND status='Shortlisted'", (sid,))
    shortlisted = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s AND status='In Process'", (sid,))
    inprocess = cur.fetchone()["c"]

    cur.execute("""
        SELECT a.application_id, d.role, c.company_name, d.ctc, a.applied_date, a.status
        FROM Applications a
        JOIN Placement_Drives d ON a.drive_id   = d.drive_id
        JOIN Companies c        ON d.company_id = c.company_id
        WHERE a.student_id=%s ORDER BY a.applied_date DESC LIMIT 5
    """, (sid,))
    recent = cur.fetchall()
    cur.close(); db.close()
    return render_template("dashboard.html", total=total, selected=selected,
                           shortlisted=shortlisted, inprocess=inprocess, recent=recent)


# ── DRIVES LISTING ───────────────────────────────
@app.route("/drives")
def drives():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM vw_drive_listing ORDER BY drive_date ASC")
    listings = cur.fetchall()

    # applicant count per drive
    cur.execute("""
        SELECT drive_id, COUNT(*) as cnt
        FROM Applications GROUP BY drive_id
    """)
    app_counts = {r["drive_id"]: r["cnt"] for r in cur.fetchall()}

    cur.close(); db.close()
    for d in listings:
        d["applicants"] = app_counts.get(d["drive_id"], 0)
        d["branches"]   = d["eligible_branches"].split(",") if d["eligible_branches"] else []

    applied_ids = []
    if session.get("role") == "student":
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT drive_id FROM Applications WHERE student_id=%s", (session["student_id"],))
        applied_ids = [r["drive_id"] for r in cur.fetchall()]
        cur.close(); db.close()

    return render_template("drives.html", listings=listings, applied_ids=applied_ids)


# ── APPLY ────────────────────────────────────────
@app.route("/apply/<int:drive_id>", methods=["POST"])
def apply(drive_id):
    if session.get("role") != "student":
        flash("Please log in to apply.", "warning")
        return redirect(url_for("login"))

    sid    = session["student_id"]
    cgpa   = session["cgpa"]
    branch = session["branch"]

    db = get_db(); cur = db.cursor(dictionary=True)

    # Block if already placed
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE student_id=%s AND status='Selected'", (sid,))
    if cur.fetchone()["c"] > 0:
        flash("You have already been placed! You cannot apply to more drives.", "warning")
        cur.close(); db.close()
        return redirect(url_for("drives"))
    cur.execute("SELECT eligibility_cgpa, eligible_branches FROM Placement_Drives WHERE drive_id=%s", (drive_id,))
    drive = cur.fetchone()

    if float(cgpa) < float(drive["eligibility_cgpa"]):
        flash(f"You don't meet the CGPA requirement ({drive['eligibility_cgpa']}).", "danger")
        cur.close(); db.close()
        return redirect(url_for("drives"))

    eligible = [b.strip() for b in drive["eligible_branches"].split(",")]
    if branch not in eligible:
        flash(f"Your branch ({branch}) is not eligible for this drive.", "danger")
        cur.close(); db.close()
        return redirect(url_for("drives"))

    try:
        cur2 = db.cursor()
        cur2.execute("""
            INSERT INTO Applications (student_id, drive_id, applied_date, status)
            VALUES (%s, %s, %s, 'Applied')
        """, (sid, drive_id, date.today()))
        db.commit()
        flash("Application submitted successfully!", "success")
    except mysql.connector.IntegrityError:
        flash("You have already applied to this drive.", "warning")
    finally:
        cur.close(); db.close()
    return redirect(url_for("my_applications"))


# ── MY APPLICATIONS ──────────────────────────────
@app.route("/applications")
def my_applications():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    sid = session["student_id"]
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.application_id, d.role, c.company_name, c.industry,
               d.ctc, d.drive_date, a.applied_date, a.status
        FROM Applications a
        JOIN Placement_Drives d ON a.drive_id   = d.drive_id
        JOIN Companies c        ON d.company_id = c.company_id
        WHERE a.student_id=%s ORDER BY a.applied_date DESC
    """, (sid,))
    apps = cur.fetchall()
    cur.close(); db.close()
    return render_template("my_applications.html", apps=apps)


# ── APPLICATION DETAIL ───────────────────────────
@app.route("/application/<int:app_id>")
def application_detail(app_id):
    if session.get("role") not in ("student","officer"):
        return redirect(url_for("home"))
    db = get_db(); cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT a.*, s.name AS student_name, s.email AS student_email,
               s.branch, s.cgpa, d.role, d.ctc, d.drive_date,
               c.company_name, d.drive_id
        FROM Applications a
        JOIN Students s         ON a.student_id = s.student_id
        JOIN Placement_Drives d ON a.drive_id   = d.drive_id
        JOIN Companies c        ON d.company_id = c.company_id
        WHERE a.application_id=%s
    """, (app_id,))
    app_data = cur.fetchone()

    cur.execute("""
        SELECT status, updated_at FROM Application_Status_History
        WHERE application_id=%s ORDER BY updated_at ASC
    """, (app_id,))
    history = cur.fetchall()

    cur.execute("""
        SELECT sr.round_id, sr.round_name, sr.round_type, sr.round_date,
               rr.result, rr.remarks
        FROM Selection_Rounds sr
        LEFT JOIN Round_Results rr
            ON sr.round_id = rr.round_id AND rr.student_id=%s
        WHERE sr.drive_id=%s ORDER BY sr.round_date ASC
    """, (app_data["student_id"], app_data["drive_id"]))
    rounds = cur.fetchall()

    cur.close(); db.close()
    return render_template("application_detail.html",
                           app=app_data, history=history, rounds=rounds)


# ── UPDATE ROUND RESULT ──────────────────────────
@app.route("/officer/update_round/<int:round_id>/<int:student_id>", methods=["POST"])
def update_round(round_id, student_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    result = request.form["result"]
    remarks = request.form.get("remarks", "")
    db = get_db(); cur = db.cursor()
    # Upsert: insert or update if exists
    cur.execute("""
        INSERT INTO Round_Results (round_id, student_id, result, remarks)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE result=%s, remarks=%s
    """, (round_id, student_id, result, remarks, result, remarks))
    db.commit()
    cur.close(); db.close()
    flash("Round result updated.", "success")
    return redirect(request.referrer or url_for("officer_dashboard"))


# ── OFFICER AUTH ─────────────────────────────────
@app.route("/officer/login", methods=["GET","POST"])
def officer_login():
    if request.method == "POST":
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM Placement_Officers WHERE email=%s AND password=%s",
                    (request.form["email"], request.form["password"]))
        officer = cur.fetchone()
        cur.close(); db.close()
        if officer:
            session["officer_id"]   = officer["officer_id"]
            session["officer_name"] = officer["name"]
            session["role"]         = "officer"
            return redirect(url_for("officer_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("officer_login.html")


@app.route("/officer/logout")
def officer_logout():
    session.clear()
    return redirect(url_for("home"))


# ── OFFICER DASHBOARD ────────────────────────────
@app.route("/officer/dashboard")
def officer_dashboard():
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    db = get_db(); cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) as c FROM Placement_Drives")
    total_drives = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications")
    total_apps = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM Applications WHERE status='Selected'")
    placed = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(DISTINCT student_id) as c FROM Applications")
    active_students = cur.fetchone()["c"]

    cur.execute("""
        SELECT d.drive_id, d.role, c.company_name, d.drive_date, d.ctc,
               COUNT(a.application_id) as applicants
        FROM Placement_Drives d
        JOIN Companies c ON d.company_id = c.company_id
        LEFT JOIN Applications a ON d.drive_id = a.drive_id
        GROUP BY d.drive_id ORDER BY d.drive_date ASC
    """)
    drives = cur.fetchall()
    cur.close(); db.close()
    return render_template("officer_dashboard.html", total_drives=total_drives,
                           total_apps=total_apps, placed=placed,
                           active_students=active_students, drives=drives)


# ── POST DRIVE ───────────────────────────────────
@app.route("/officer/post_drive", methods=["GET","POST"])
def post_drive():
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    if request.method == "POST":
        d = request.form
        branches = ",".join(request.form.getlist("branches"))
        db = get_db(); cur = db.cursor()
        cur.execute("""
            INSERT INTO Placement_Drives
            (company_id, officer_id, role, ctc, drive_date, eligibility_cgpa, eligible_branches)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (d["company_id"], session["officer_id"], d["role"],
              d["ctc"], d["drive_date"], d["eligibility_cgpa"], branches))
        db.commit()
        cur.close(); db.close()
        flash("Placement drive posted successfully!", "success")
        return redirect(url_for("officer_dashboard"))

    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT company_id, company_name FROM Companies ORDER BY company_name")
    companies = cur.fetchall()
    cur.execute("SELECT location_id, city, state FROM Locations ORDER BY city")
    locations = cur.fetchall()
    cur.close(); db.close()
    return render_template("post_drive.html", companies=companies, locations=locations)


# ── VIEW APPLICANTS ──────────────────────────────
@app.route("/officer/applicants/<int:drive_id>")
def view_applicants(drive_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    db = get_db(); cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT d.role, c.company_name FROM Placement_Drives d
        JOIN Companies c ON d.company_id = c.company_id
        WHERE d.drive_id=%s
    """, (drive_id,))
    drive = cur.fetchone()

    cur.execute("""
        SELECT a.application_id, s.name, s.email, s.branch, s.cgpa,
               s.backlogs, a.applied_date, a.status
        FROM Applications a
        JOIN Students s ON a.student_id = s.student_id
        WHERE a.drive_id=%s ORDER BY s.cgpa DESC
    """, (drive_id,))
    applicants = cur.fetchall()

    cur.execute("""
        SELECT round_id, round_name, round_type, round_date
        FROM Selection_Rounds WHERE drive_id=%s ORDER BY round_date ASC
    """, (drive_id,))
    rounds = cur.fetchall()

    cur.close(); db.close()
    return render_template("view_applicants.html", drive=drive,
                           applicants=applicants, drive_id=drive_id, rounds=rounds)


# ── ADD SELECTION ROUND ──────────────────────────
@app.route("/officer/add_round/<int:drive_id>", methods=["POST"])
def add_round(drive_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    d = request.form
    db = get_db(); cur = db.cursor()
    cur.execute("""
        INSERT INTO Selection_Rounds (drive_id, round_name, round_type, round_date)
        VALUES (%s, %s, %s, %s)
    """, (drive_id, d["round_name"], d["round_type"], d["round_date"]))
    db.commit()
    cur.close(); db.close()
    flash("Selection round added!", "success")
    return redirect(url_for("view_applicants", drive_id=drive_id))


# ── DELETE DRIVE ──────────────────────────────────
@app.route("/officer/delete_drive/<int:drive_id>", methods=["POST"])
def delete_drive(drive_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    db = get_db(); cur = db.cursor()
    # Delete applications for this drive (cascade handles status history)
    cur.execute("DELETE FROM Applications WHERE drive_id=%s", (drive_id,))
    # Selection_Rounds has ON DELETE CASCADE, so deleting drive removes rounds & results
    cur.execute("DELETE FROM Placement_Drives WHERE drive_id=%s", (drive_id,))
    db.commit()
    cur.close(); db.close()
    flash("Placement drive deleted.", "success")
    return redirect(url_for("officer_dashboard"))


# ── ADD COMPANY ──────────────────────────────────
@app.route("/officer/add_company", methods=["POST"])
def add_company():
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    d = request.form
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO Companies (company_name, industry, location_id)
            VALUES (%s, %s, %s)
        """, (d["company_name"], d["industry"], d["location_id"]))
        db.commit()
        flash("Company added successfully!", "success")
    except mysql.connector.IntegrityError:
        flash("Company already exists.", "warning")
    finally:
        cur.close(); db.close()
    return redirect(url_for("post_drive"))


# ── DELETE COMPANY ───────────────────────────────
@app.route("/officer/delete_company/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    db = get_db(); cur = db.cursor(dictionary=True)
    # Check if any drives reference this company
    cur.execute("SELECT COUNT(*) as c FROM Placement_Drives WHERE company_id=%s", (company_id,))
    if cur.fetchone()["c"] > 0:
        flash("Cannot delete — this company has active placement drives. Delete those first.", "danger")
    else:
        cur2 = db.cursor()
        cur2.execute("DELETE FROM Companies WHERE company_id=%s", (company_id,))
        db.commit()
        cur2.close()
        flash("Company deleted.", "success")
    cur.close(); db.close()
    return redirect(url_for("post_drive"))


# ── UPDATE STATUS ────────────────────────────────
@app.route("/officer/update_status/<int:app_id>", methods=["POST"])
def update_status(app_id):
    if session.get("role") != "officer":
        return redirect(url_for("officer_login"))
    db = get_db(); cur = db.cursor()
    cur.callproc("sp_update_status", (app_id, request.form["status"]))
    db.commit()
    cur.close(); db.close()
    flash("Status updated.", "success")
    return redirect(request.referrer or url_for("officer_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
