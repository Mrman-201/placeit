"""
AI PLACEMENT MENTOR — Blueprint
Provides resume-based AI career advisory for students.

Uses PyMuPDF for PDF text extraction and Groq API (LLama 3.3 70B)
for generating personalised career analysis.
"""

import os
import tempfile
import traceback

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, flash
)
import fitz  # PyMuPDF
import mysql.connector
from groq import Groq

# ── Blueprint ────────────────────────────────────
ai_mentor_bp = Blueprint("ai_mentor", __name__)

# ── DB helper (mirrors app.py) ───────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",           # ← same as app.py
    "database": "placement_db"
}

def _get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ── PDF helpers ──────────────────────────────────
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _extract_pdf_text(file_storage):
    """Save uploaded file to a temp path, extract text, delete temp file."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        file_storage.save(tmp_path)
        # Validate size
        if os.path.getsize(tmp_path) > MAX_FILE_SIZE:
            return None, "File exceeds the 5 MB limit."
        doc = fitz.open(tmp_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if not text.strip():
            return None, "Could not extract any text from the PDF. Is it a scanned image?"
        return text.strip(), None
    except Exception as exc:
        return None, f"Failed to read PDF: {exc}"
    finally:
        os.close(tmp_fd)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Student data from DB ─────────────────────────
def _fetch_student_profile(student_id):
    """Return a dict with all student info from MySQL."""
    db = _get_db()
    cur = db.cursor(dictionary=True)

    # Basic info
    cur.execute("SELECT * FROM Students WHERE student_id=%s", (student_id,))
    student = cur.fetchone()

    # Skills
    cur.execute("""
        SELECT sk.skill_name
        FROM Student_Skills ss
        JOIN Skills sk ON ss.skill_id = sk.skill_id
        WHERE ss.student_id=%s ORDER BY sk.skill_name
    """, (student_id,))
    skills = [r["skill_name"] for r in cur.fetchall()]

    # Applications with company & role details
    cur.execute("""
        SELECT a.status, d.role, c.company_name, d.ctc, a.applied_date
        FROM Applications a
        JOIN Placement_Drives d ON a.drive_id   = d.drive_id
        JOIN Companies c        ON d.company_id = c.company_id
        WHERE a.student_id=%s ORDER BY a.applied_date DESC
    """, (student_id,))
    applications = cur.fetchall()

    cur.close()
    db.close()

    return {
        "name":         student["name"],
        "email":        student["email"],
        "branch":       student["branch"],
        "year":         student["year"],
        "cgpa":         float(student["cgpa"]),
        "backlogs":     student["backlogs"],
        "city":         student.get("city", ""),
        "state":        student.get("state", ""),
        "skills":       skills,
        "applications": applications,
    }


# ── Prompt engineering ───────────────────────────
def _build_prompt(resume_text, profile):
    """Build a detailed system + user prompt for the LLM."""

    # Summarise application history
    app_lines = []
    for a in profile["applications"]:
        ctc_lpa = float(a["ctc"]) / 100000
        app_lines.append(
            f"  - {a['role']} at {a['company_name']} "
            f"(CTC ₹{ctc_lpa:.1f} LPA) — Status: {a['status']}"
        )
    app_summary = "\n".join(app_lines) if app_lines else "  No applications yet."

    system_prompt = """You are an elite career advisory panel combining the expertise of:
1. A Senior Technical Recruiter with 15+ years of hiring experience at top tech companies (Google, Microsoft, Amazon).
2. A Career Mentor who has guided 1000+ students into their first tech roles.
3. A Placement Officer at a top engineering college who understands campus hiring.
4. A Resume Reviewer certified in ATS optimisation and modern resume best practices.

Your task is to analyse a student's resume AND their academic/placement database profile to produce a comprehensive, highly personalised career advisory report.

CRITICAL INSTRUCTIONS:
- Be specific, not generic. Reference actual skills, projects, and details from the resume.
- Tailor every recommendation to this student's branch, CGPA, skills, and experience level.
- Use Indian placement/hiring context (campus drives, CTC in LPA, service-based vs product-based companies).
- Be encouraging but honest about gaps.
- Use markdown formatting with proper headings and bullet points.

You MUST structure your response with EXACTLY these sections in this order:

## 📊 Overall Resume Score
Give a score out of 100. Then explain the reasoning behind the score in 3-4 bullet points.

## 📝 Career Summary
A concise 3-4 sentence summary of the student's current profile, strengths, and positioning in the job market.

## 🎯 Best Suitable Roles
List 4-6 specific roles (e.g., Backend Developer, ML Engineer, Data Analyst). For each role, explain in 1-2 sentences WHY this student is suited for it based on their actual skills and experience.

## 💪 Strengths
List 5-7 strengths, both technical and non-technical, inferred from the resume and profile. Be specific.

## ⚠️ Missing Technical Skills
List 5-7 skills the student should learn. For each skill, explain in one sentence why it matters for their target roles.

## 🗺️ Personalized Learning Roadmap

### Next 30 Days
List 3-4 specific learning priorities with concrete technologies/topics.

### Next 60 Days
List 3-4 intermediate goals building on the 30-day plan.

### Next 90 Days
List 3-4 advanced goals that make the student job-ready.

## 🛠️ Recommended Projects
Suggest 4-5 portfolio-quality projects the student can build. Each should have a title and 1-2 sentence description of what it demonstrates.

## 🏅 Recommended Certifications
Suggest 3-5 certifications that are actually valuable (not filler). Include the provider and why it matters.

## 🏢 Companies to Target
Recommend 6-8 companies suitable for this student's profile. Group them into "Dream", "Target", and "Safety" categories. Include why each is a good fit.

## 📄 Resume Improvement Suggestions
Provide 5-7 actionable improvements such as: better project descriptions, missing achievements, ATS keywords, formatting tips, quantified impact bullets.

## 🎓 Placement Preparation Tips
Provide 5-7 personalised placement preparation tips based on the student's specific profile, upcoming drives, and skill gaps.
"""

    user_prompt = f"""STUDENT DATABASE PROFILE:
- Name: {profile['name']}
- Branch: {profile['branch']}
- Year: {profile['year']}
- CGPA: {profile['cgpa']}/10.0
- Active Backlogs: {profile['backlogs']}
- Location: {profile['city']}, {profile['state']}
- Registered Skills: {', '.join(profile['skills']) if profile['skills'] else 'None listed'}

PLACEMENT APPLICATION HISTORY:
{app_summary}

---

RESUME CONTENT (extracted from uploaded PDF):
\"\"\"
{resume_text[:6000]}
\"\"\"

Now analyse this student's complete profile and resume. Produce the full career advisory report following the exact section structure specified."""

    return system_prompt, user_prompt


# ── Groq API call ────────────────────────────────
def _call_groq(system_prompt, user_prompt):
    """Send the prompt to Groq and return the response text."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return None, "Groq API key is not configured. Please add your key to the .env file."

    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.35,
            max_tokens=4096,
            timeout=60,
        )

        if not chat_completion.choices:
            return None, "The AI returned an empty response. Please try again."

        content = chat_completion.choices[0].message.content
        if not content or not content.strip():
            return None, "The AI returned a blank response. Please try again."

        return content.strip(), None

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[AI Mentor] Groq API error:\n{tb}")
        return None, f"AI service error: {exc}"


# ── Parse AI response into sections ──────────────
def _parse_sections(ai_text):
    """Split the markdown AI response into labelled sections."""
    import re

    section_map = {
        "resume_score":       "Overall Resume Score",
        "career_summary":     "Career Summary",
        "suitable_roles":     "Best Suitable Roles",
        "strengths":          "Strengths",
        "missing_skills":     "Missing Technical Skills",
        "learning_roadmap":   "Personalized Learning Roadmap",
        "projects":           "Recommended Projects",
        "certifications":     "Recommended Certifications",
        "companies":          "Companies to Target",
        "resume_improvements": "Resume Improvement Suggestions",
        "placement_tips":     "Placement Preparation Tips",
    }

    # Split on ## headings
    parts = re.split(r'\n(?=##\s)', ai_text)
    sections = {}

    for key, title_keyword in section_map.items():
        for part in parts:
            # Match heading (with or without emoji)
            first_line = part.strip().split("\n")[0]
            if title_keyword.lower() in first_line.lower():
                # Remove the heading line itself and keep the body
                body = "\n".join(part.strip().split("\n")[1:]).strip()
                sections[key] = body
                break
        if key not in sections:
            sections[key] = ""

    # Try to extract the numeric score (multiple patterns for robustness)
    score = 0
    score_text = sections.get("resume_score", "")
    # Also check the full AI response in case the section wasn't parsed
    search_text = score_text if score_text else ai_text

    # Pattern 1: "72/100" or "72 / 100" (with optional bold markers)
    m = re.search(r'\*{0,2}(\d{1,3})\*{0,2}\s*/\s*\*{0,2}100\*{0,2}', search_text)
    if not m:
        # Pattern 2: "72 out of 100"
        m = re.search(r'(\d{1,3})\s+out\s+of\s+100', search_text, re.IGNORECASE)
    if not m:
        # Pattern 3: "Score: 72" or "Score - 72" or "score of 72"
        m = re.search(r'score\s*[:\-–]\s*\*{0,2}(\d{1,3})\*{0,2}', search_text, re.IGNORECASE)
    if not m:
        # Pattern 4: Any number followed by "/100" or "/ 100" anywhere
        m = re.search(r'(\d{1,3})\s*/\s*100', search_text)
    if not m:
        # Pattern 5: Fallback — first 2-digit number in the score section
        m = re.search(r'\b(\d{2})\b', score_text)

    if m:
        score = min(int(m.group(1)), 100)
    sections["score_number"] = score

    return sections


# ═══════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════

@ai_mentor_bp.route("/ai-mentor")
def ai_mentor_page():
    """Render the upload page."""
    if session.get("role") != "student":
        flash("Please log in as a student to access AI Mentor.", "warning")
        return redirect(url_for("login"))
    return render_template("ai_mentor.html")


@ai_mentor_bp.route("/ai-mentor/analyze", methods=["POST"])
def ai_mentor_analyze():
    """Handle resume upload, process, call AI, render results."""
    if session.get("role") != "student":
        flash("Please log in as a student.", "warning")
        return redirect(url_for("login"))

    # ── File validation ──
    if "resume" not in request.files:
        flash("No file uploaded. Please select a PDF resume.", "danger")
        return redirect(url_for("ai_mentor.ai_mentor_page"))

    file = request.files["resume"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("ai_mentor.ai_mentor_page"))

    if not _allowed_file(file.filename):
        flash("Only PDF files are accepted. Please upload a .pdf file.", "danger")
        return redirect(url_for("ai_mentor.ai_mentor_page"))

    # ── Extract text ──
    resume_text, err = _extract_pdf_text(file)
    if err:
        flash(err, "danger")
        return redirect(url_for("ai_mentor.ai_mentor_page"))

    # ── Fetch student profile from DB ──
    student_id = session["student_id"]
    profile = _fetch_student_profile(student_id)

    # ── Build prompt & call Groq ──
    system_prompt, user_prompt = _build_prompt(resume_text, profile)
    ai_response, err = _call_groq(system_prompt, user_prompt)
    if err:
        flash(err, "danger")
        return redirect(url_for("ai_mentor.ai_mentor_page"))

    # ── Parse sections ──
    sections = _parse_sections(ai_response)

    return render_template(
        "ai_mentor.html",
        results=True,
        sections=sections,
        profile=profile,
        raw_response=ai_response,
    )
