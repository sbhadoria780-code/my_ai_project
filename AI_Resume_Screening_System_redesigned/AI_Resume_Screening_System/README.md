# AI Resume Screening System

A transparent, rule-based resume screening app built with Flask. Scores are
explainable (not a black-box model), PII is stripped before scoring, and
every hiring decision is made by a human reviewer and logged for audit.

## Quick start

```bash
cd AI_Resume_Screening_System
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in your browser.

## How it works

1. **Define the role** — job title, required skills (comma-separated),
   minimum years of experience, minimum education level.
2. **Upload resumes** — `.pdf`, `.docx`, or `.txt`, multiple at once.
3. The system:
   - Extracts text (`utils/pdf_parser.py`)
   - Strips PII/bias-risk signals — name, email, phone, address, age/DOB,
     graduation year — **before** scoring (`utils/text_cleaner.py`)
   - Extracts skills, experience years, and education level via transparent
     keyword/regex matching (`utils/skill_extractor.py`)
   - Compares against your stated requirements (`utils/matcher.py`)
   - Computes a weighted, fully explainable score (`utils/scorer.py`)
4. **Results page** — candidates ranked by score, with a status badge.
   Ranking is advisory only.
5. **Candidate detail page** — full score breakdown (matched/missing
   skills, experience, education), the extracted resume text, and a
   **human review form** (reviewer name, decision, notes — required).
   No candidate is ever auto-rejected by the system itself.
6. **Audit export** — download a CSV of every candidate's score and the
   human decision made on them, for compliance record-keeping.

## Responsible-AI defaults built in

- **No training on historical hiring data.** Scoring weights are fixed
  constants you can read and edit in `utils/scorer.py`, not learned from
  your past hiring outcomes — this avoids the most common real-world
  source of resume-screening bias (a model learning to replicate a
  company's historical human bias).
- **Anonymization before scoring.** See `anonymize_text()` in
  `utils/text_cleaner.py`.
- **Human-in-the-loop is mandatory.** The only way a candidate's status
  changes from "Pending Review" is a human submitting the review form.
- **Full audit trail.** Every scoring event and every human decision is
  timestamped in the `audit_log` table and exportable as CSV.

## Before using this on real candidates

This is a starter system, not a compliance guarantee. Depending on your
jurisdiction, you may be legally required to:

- Run an **independent bias/impact-ratio audit** before deployment and
  at least annually (e.g. NYC Local Law 144's "four-fifths rule" test).
- Give candidates **advance notice** that AI is used in screening, and a
  way to request accommodations or human review (e.g. California's
  automated decision-making rules, EU AI Act high-risk obligations).
- **Retain audit records** for a set number of years (several US states
  now require this).
- Avoid using AI tools that could act as your "agent" in a way that
  creates liability under anti-discrimination law even if a vendor built
  the tool — courts have begun allowing exactly this theory to proceed.

Consult an employment lawyer familiar with your jurisdiction(s) before
using this (or any resume screening tool) on real applicants.

## Extending it

- **Add more skills**: edit `DEFAULT_SKILLS_DB` in
  `utils/skill_extractor.py`, or load it from a JSON file / database
  table if you want it configurable through the UI.
- **Swap the scoring model**: `compute_score()` in `utils/scorer.py` is
  the single place overall score is calculated — replace the weighted
  formula with a different rubric as needed, but keep returning a
  breakdown/explanation alongside any score.
- **Add authentication**: this starter app has no login system. Add one
  (e.g. Flask-Login) before deploying anywhere beyond your own machine,
  since resume data and audit logs are sensitive.
- **Swap SQLite for Postgres/MySQL** for multi-user or production use —
  the `get_db()` / `init_db()` functions in `app.py` are the only place
  that needs to change.
