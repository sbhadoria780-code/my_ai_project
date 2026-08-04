"""
skill_extractor.py
-------------------
Extracts structured, job-relevant signals from resume text:
skills, years of experience, and education level.

Everything here is transparent keyword/regex matching rather than a
black-box model -- so every score the system produces can be traced
back to a specific matched phrase. That traceability is what makes
the system auditable and explainable to a candidate who asks "why
was I screened out?" (or, better, to the human recruiter who is
making the actual decision).
"""

import re

# A starter skills taxonomy. Extend this list (or load from a JSON /
# database table) to fit your industry. Keep it job-relevant only --
# never include terms that function as proxies for protected
# characteristics (e.g. names of historically single-gender colleges,
# fraternal/religious organizations, etc.)
DEFAULT_SKILLS_DB = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    # Web / frameworks
    "react", "angular", "vue", "django", "flask", "spring boot", "node.js",
    "express.js", "next.js", "asp.net", "html", "css", "tailwind",
    # Data / ML
    "sql", "postgresql", "mysql", "mongodb", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "keras", "power bi", "tableau", "excel",
    "machine learning", "deep learning", "nlp", "data analysis", "etl",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd",
    "jenkins", "git", "linux", "bash",
    # Project / soft-skill-adjacent hard skills (kept concrete, not vague traits)
    "agile", "scrum", "jira", "project management", "product management",
    # Business / general office
    "salesforce", "sap", "quickbooks", "erp", "crm",
]

EDUCATION_LEVELS = {
    "phd": 5, "doctorate": 5,
    "master": 4, "m.s.": 4, "msc": 4, "mba": 4, "m.tech": 4,
    "bachelor": 3, "b.s.": 3, "bsc": 3, "b.tech": 3, "b.e.": 3, "ba ": 3,
    "associate degree": 2, "diploma": 2,
    "high school": 1,
}

EXPERIENCE_RE = re.compile(
    r"(\d{1,2})\+?\s*(?:years|yrs)\b(?:\s*of)?\s*(?:experience|exp)?",
    re.IGNORECASE,
)


def extract_skills(text: str, skills_db=None) -> set:
    """Return the set of skills (from skills_db) found in the text."""
    if skills_db is None:
        skills_db = DEFAULT_SKILLS_DB
    text_lower = f" {text.lower()} "
    found = set()
    for skill in skills_db:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.add(skill)
    return found


def extract_experience_years(text: str) -> int:
    """
    Best-effort estimate of total years of experience, based on
    explicit "X years of experience" style phrases. Returns the
    MAXIMUM figure found (resumes often restate this near the top).
    Returns 0 if no explicit figure is found -- callers should treat
    0 as "unknown", not "no experience", and rely on human review for
    edge cases.
    """
    matches = EXPERIENCE_RE.findall(text)
    years = [int(m) for m in matches if m.isdigit()]
    return max(years) if years else 0


def extract_education_level(text: str) -> tuple:
    """
    Returns (level_name, level_score) for the highest education
    credential mentioned. level_score ranges 0 (none detected) - 5 (PhD).
    """
    text_lower = text.lower()
    best_level, best_score = "not specified", 0
    for keyword, score in EDUCATION_LEVELS.items():
        if keyword in text_lower and score > best_score:
            best_level, best_score = keyword.strip(". "), score
    return best_level, best_score
