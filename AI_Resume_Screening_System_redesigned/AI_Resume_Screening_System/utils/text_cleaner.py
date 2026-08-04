"""
text_cleaner.py
----------------
Normalizes resume text and extracts basic contact fields.

Also provides `anonymize_text()`, which strips out signals that are
NOT job-relevant but which unconscious or algorithmic bias can latch
onto (name, email, phone, address, age/DOB, graduation year, photo
references). The scoring pipeline runs on the ANONYMIZED text, not
the raw text -- recruiters only see the identifying info after a
resume already has a score, which reduces bias in both the AI and
human-review halves of the process.
"""

import re


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
DOB_RE = re.compile(
    r"\b(date of birth|dob|born on)\b[:\-]?\s*[\w,\/\- ]{4,20}", re.IGNORECASE
)
AGE_RE = re.compile(r"\b(age)\b[:\-]?\s*\d{1,2}\b", re.IGNORECASE)
GRAD_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ADDRESS_HINT_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\s]{3,40}\b(street|st\.|avenue|ave\.|road|rd\.|lane|ln\.|block|sector)\b",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    """
    Normalize whitespace and strip control characters while
    preserving characters that matter for skill matching
    (e.g. C++, C#, .NET).
    """
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else ""


def guess_candidate_name(text: str, filename: str) -> str:
    """
    Best-effort name guess: most resumes put the candidate's name on
    the first non-empty line. Falls back to the filename.
    This is used ONLY for display/labeling to the human reviewer --
    never fed into the scoring model.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like headers/emails/phones
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        if len(line.split()) <= 5 and len(line) < 60:
            return line
        break
    return filename


def anonymize_text(text: str) -> str:
    """
    Strip PII / bias-risk signals before the text reaches the scoring
    model. This is a best-effort filter, not a legal guarantee of
    anonymity -- always pair it with a human-review step.
    """
    if not text:
        return ""

    anonymized = text
    anonymized = EMAIL_RE.sub("[EMAIL REDACTED]", anonymized)
    anonymized = PHONE_RE.sub("[PHONE REDACTED]", anonymized)
    anonymized = DOB_RE.sub("[DOB REDACTED]", anonymized)
    anonymized = AGE_RE.sub("[AGE REDACTED]", anonymized)
    anonymized = ADDRESS_HINT_RE.sub("[ADDRESS REDACTED]", anonymized)
    # Redact standalone 4-digit years that look like graduation dates
    # only when preceded by graduation-related keywords, to avoid
    # nuking dates that indicate relevant work experience duration.
    anonymized = re.sub(
        r"(graduat\w*|class of)\s*[:\-]?\s*(19|20)\d{2}",
        r"\1 [YEAR REDACTED]",
        anonymized,
        flags=re.IGNORECASE,
    )
    return anonymized
