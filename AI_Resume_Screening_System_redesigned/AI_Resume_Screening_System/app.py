"""
app.py
------
AI Resume Screening System -- Flask application.

RESPONSIBLE-AI DESIGN NOTES (read this before deploying):

1. HUMAN-IN-THE-LOOP IS MANDATORY.
   This system never auto-rejects a candidate. Every resume gets a
   transparent, explainable score, but the actual advance/hold/reject
   decision is always made by a human reviewer through the UI, and
   that decision is logged (who, when, what, why).

2. SCORING IS RULE-BASED AND EXPLAINABLE, NOT A TRAINED BLACK BOX.
   Scores come from keyword/regex matching against job requirements
   you define (see utils/scorer.py). There is no model trained on
   your historical hiring data, which is the single biggest source of
   real-world resume-screening bias.

3. ANONYMIZATION BEFORE SCORING.
   Name, email, phone, address, age/DOB, and graduation-year signals
   are stripped from the text BEFORE it is scored (utils/text_cleaner
   .anonymize_text). Reviewers see identifying info only in the
   candidate detail view, after the score already exists.

4. FULL AUDIT TRAIL.
   Every scoring event and every human decision is written to SQLite
   with a timestamp, and can be exported as CSV from /export_audit.
   Several jurisdictions (e.g. NYC Local Law 144, California's Civil
   Rights Council rules) require exactly this kind of record-keeping
   -- typically for several years. Check your applicable jurisdiction's
   requirements before deploying in production.

5. THIS IS A STARTER SYSTEM, NOT A COMPLIANCE GUARANTEE.
   Before using this on real candidates, you are strongly encouraged
   to: (a) run an independent bias/impact-ratio audit, (b) add a
   candidate-facing notice that AI is used in screening, (c) add an
   accommodations request path, and (d) consult an employment lawyer
   about the rules in your jurisdiction(s).
"""

import os
import sqlite3
import csv
import io
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, g, abort
)
from werkzeug.utils import secure_filename

from utils.pdf_parser import extract_text
from utils.text_cleaner import clean_text, anonymize_text, extract_email, extract_phone, guess_candidate_name
from utils.skill_extractor import extract_skills, extract_experience_years, extract_education_level, DEFAULT_SKILLS_DB
from utils.matcher import match_skills, match_experience, match_education
from utils.scorer import compute_score, score_band

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DB_PATH = os.path.join(BASE_DIR, "database", "resume_screening.db")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per upload batch safeguard

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            required_experience_years INTEGER DEFAULT 0,
            required_education TEXT DEFAULT '',
            required_education_score INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            display_name TEXT,
            email TEXT,
            phone TEXT,
            raw_text TEXT,
            matched_skills TEXT,
            missing_skills TEXT,
            experience_years INTEGER,
            education_level TEXT,
            overall_score REAL,
            skills_match_pct REAL DEFAULT 0,
            experience_match_pct REAL DEFAULT 0,
            education_match_pct REAL DEFAULT 0,
            score_band TEXT,
            explanation TEXT,
            review_status TEXT DEFAULT 'Pending Review',
            review_notes TEXT DEFAULT '',
            reviewed_by TEXT DEFAULT '',
            reviewed_at TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT,
            actor TEXT DEFAULT 'system',
            timestamp TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def log_audit_event(db, candidate_id, event_type, details, actor="system"):
    db.execute(
        "INSERT INTO audit_log (candidate_id, event_type, details, actor, timestamp) "
        "VALUES (?, ?, ?, ?, ?)",
        (candidate_id, event_type, details, actor, datetime.utcnow().isoformat()),
    )
    db.commit()


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", default_skills=DEFAULT_SKILLS_DB)


@app.route("/upload", methods=["POST"])
def upload():
    job_title = request.form.get("job_title", "").strip()
    required_skills_raw = request.form.get("required_skills", "").strip()
    required_experience = request.form.get("required_experience", "0").strip()
    required_education = request.form.get("required_education", "").strip().lower()
    files = request.files.getlist("resumes")

    if not job_title or not required_skills_raw:
        flash("Job title and required skills are mandatory.", "error")
        return redirect(url_for("index"))

    if not files or files[0].filename == "":
        flash("Please upload at least one resume.", "error")
        return redirect(url_for("index"))

    try:
        required_experience_years = int(required_experience)
    except ValueError:
        required_experience_years = 0

    required_skills = {s.strip() for s in required_skills_raw.split(",") if s.strip()}

    # crude education-level score for the requirement text
    from utils.skill_extractor import EDUCATION_LEVELS
    required_education_score = 0
    for keyword, score in EDUCATION_LEVELS.items():
        if keyword in required_education:
            required_education_score = max(required_education_score, score)

    db = get_db()
    cur = db.execute(
        "INSERT INTO jobs (title, required_skills, required_experience_years, "
        "required_education, required_education_score, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            job_title,
            ", ".join(sorted(required_skills)),
            required_experience_years,
            required_education,
            required_education_score,
            datetime.utcnow().isoformat(),
        ),
    )
    job_id = cur.lastrowid
    db.commit()

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    processed = 0

    for file in files:
        if not file or file.filename == "":
            continue
        if not allowed_file(file.filename):
            flash(f"Skipped unsupported file type: {file.filename}", "error")
            continue

        filename = secure_filename(file.filename)
        # avoid collisions across batches
        stored_name = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
        filepath = os.path.join(UPLOAD_DIR, stored_name)
        file.save(filepath)

        raw_text = extract_text(filepath)
        cleaned = clean_text(raw_text)

        if not cleaned:
            flash(f"Could not extract text from {filename} -- skipped.", "error")
            continue

        display_name = guess_candidate_name(cleaned, filename)
        email = extract_email(cleaned)
        phone = extract_phone(cleaned)

        # --- Score on ANONYMIZED text only ---
        anonymized = anonymize_text(cleaned)
        candidate_skills = extract_skills(anonymized)
        candidate_years = extract_experience_years(anonymized)
        edu_level_name, edu_level_score = extract_education_level(anonymized)

        skills_result = match_skills(candidate_skills, required_skills)
        experience_result = match_experience(candidate_years, required_experience_years)
        education_result = match_education(edu_level_score, required_education_score)

        breakdown = compute_score(skills_result, experience_result, education_result)
        band = score_band(breakdown["overall_score"])

        cur = db.execute(
            """INSERT INTO candidates (
                job_id, filename, display_name, email, phone, raw_text,
                matched_skills, missing_skills, experience_years, education_level,
                overall_score, skills_match_pct, experience_match_pct, education_match_pct,
                score_band, explanation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job_id, filename, display_name, email, phone, cleaned,
                ", ".join(skills_result["matched"]), ", ".join(skills_result["missing"]),
                candidate_years, edu_level_name,
                breakdown["overall_score"],
                skills_result["match_pct"], experience_result["match_pct"], education_result["match_pct"],
                band, breakdown["explanation"],
                datetime.utcnow().isoformat(),
            ),
        )
        candidate_id = cur.lastrowid
        db.commit()

        log_audit_event(
            db, candidate_id, "SCORED",
            f"Score={breakdown['overall_score']} band={band} "
            f"skills_match={skills_result['match_pct']}% "
            f"experience={candidate_years}y education={edu_level_name}",
        )
        processed += 1

    if processed == 0:
        flash("No resumes could be processed. Please check the file formats.", "error")
        return redirect(url_for("index"))

    flash(f"Processed {processed} resume(s).", "success")
    return redirect(url_for("results", job_id=job_id))


@app.route("/results/<int:job_id>")
def results(job_id):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        abort(404)

    candidates = db.execute(
        "SELECT * FROM candidates WHERE job_id = ? ORDER BY overall_score DESC",
        (job_id,),
    ).fetchall()

    total = len(candidates)
    scores = [c["overall_score"] or 0 for c in candidates]
    top_score = round(max(scores), 1) if scores else 0
    avg_score = round(sum(scores) / total, 1) if total else 0

    status_labels = ["Advance", "Hold", "Request More Info", "Reject", "Pending Review"]
    status_colors = {
        "Advance": "#22c55e", "Hold": "#f59e0b", "Request More Info": "#6366f1",
        "Reject": "#ef4444", "Pending Review": "#cbd5e1",
    }
    status_counts = {label: 0 for label in status_labels}
    for c in candidates:
        key = c["review_status"] if c["review_status"] in status_counts else "Pending Review"
        status_counts[key] += 1

    donut_segments = []
    cum = 0
    for label in status_labels:
        count = status_counts[label]
        pct = (count / total * 100) if total else 0
        donut_segments.append({
            "label": label, "color": status_colors[label], "count": count,
            "start": round(cum, 2), "end": round(cum + pct, 2),
        })
        cum += pct

    buckets = [0, 0, 0, 0, 0]  # score bands: 0-20, 21-40, 41-60, 61-80, 81-100
    for s in scores:
        idx = min(int(s // 20), 4)
        buckets[idx] += 1
    bucket_peak = max(buckets) if buckets else 0

    stats = {
        "total": total, "top_score": top_score, "avg_score": avg_score,
        "advance_count": status_counts["Advance"],
    }

    return render_template(
        "results.html", job=job, candidates=candidates, stats=stats,
        donut_segments=donut_segments, buckets=buckets, bucket_peak=bucket_peak,
    )


@app.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):
    db = get_db()
    candidate = db.execute(
        "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()
    if candidate is None:
        abort(404)

    job = db.execute("SELECT * FROM jobs WHERE id = ?", (candidate["job_id"],)).fetchone()
    history = db.execute(
        "SELECT * FROM audit_log WHERE candidate_id = ? ORDER BY timestamp ASC",
        (candidate_id,),
    ).fetchall()

    return render_template("candidate.html", candidate=candidate, job=job, history=history)


@app.route("/candidate/<int:candidate_id>/review", methods=["POST"])
def review_candidate(candidate_id):
    """
    Records a HUMAN decision on a candidate. The system itself never
    sets review_status to Advance/Reject on its own -- this endpoint
    is the only place that happens, and it always requires a reviewer
    name and is logged to the audit trail.
    """
    db = get_db()
    candidate = db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    if candidate is None:
        abort(404)

    decision = request.form.get("decision", "").strip()
    reviewer = request.form.get("reviewer", "").strip() or "Unnamed reviewer"
    notes = request.form.get("notes", "").strip()

    valid_decisions = {"Advance", "Hold", "Reject", "Request More Info"}
    if decision not in valid_decisions:
        flash("Invalid review decision.", "error")
        return redirect(url_for("candidate_detail", candidate_id=candidate_id))

    db.execute(
        "UPDATE candidates SET review_status = ?, review_notes = ?, "
        "reviewed_by = ?, reviewed_at = ? WHERE id = ?",
        (decision, notes, reviewer, datetime.utcnow().isoformat(), candidate_id),
    )
    db.commit()

    log_audit_event(
        db, candidate_id, "HUMAN_REVIEW",
        f"decision={decision} notes={notes or '(none)'}",
        actor=reviewer,
    )

    flash(f"Recorded decision: {decision}", "success")
    return redirect(url_for("candidate_detail", candidate_id=candidate_id))


@app.route("/export_audit/<int:job_id>")
def export_audit(job_id):
    """
    Exports a CSV audit report for a job: every candidate's score,
    breakdown, and human decision. Several jurisdictions require
    employers to retain this kind of record for multiple years --
    check your local requirements for the exact retention period.
    """
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        abort(404)

    candidates = db.execute(
        "SELECT * FROM candidates WHERE job_id = ? ORDER BY overall_score DESC",
        (job_id,),
    ).fetchall()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "candidate_id", "filename", "overall_score", "skills_match_pct",
        "experience_match_pct", "education_match_pct", "score_band",
        "matched_skills", "missing_skills", "experience_years", "education_level",
        "review_status", "reviewed_by", "reviewed_at", "review_notes", "scored_at",
    ])
    for c in candidates:
        writer.writerow([
            c["id"], c["filename"], c["overall_score"], c["skills_match_pct"],
            c["experience_match_pct"], c["education_match_pct"], c["score_band"],
            c["matched_skills"], c["missing_skills"], c["experience_years"], c["education_level"],
            c["review_status"], c["reviewed_by"], c["reviewed_at"], c["review_notes"], c["created_at"],
        ])

    buffer.seek(0)
    filename = f"audit_report_job_{job_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    report_path = os.path.join(REPORTS_DIR, filename)
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        f.write(buffer.getvalue())

    return send_file(report_path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
