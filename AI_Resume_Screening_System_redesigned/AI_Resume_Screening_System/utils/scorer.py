"""
scorer.py
---------
Combines the individual match components (skills, experience,
education) into one overall score, using fixed, documented weights.

Responsible-AI design choices baked into this module:
  1. Weights are constants declared at the top of the file, not
     learned from historical hiring data -- so the system cannot
     silently absorb and amplify a company's past hiring bias.
  2. The function always returns a `breakdown` alongside the score,
     so nothing is a black box: a recruiter (or a candidate who asks)
     can see exactly why a score came out the way it did.
  3. This module NEVER returns a hiring decision (e.g. "reject").
     It only returns a score + reasoning. The decision is always
     made by a human in app.py's review workflow.
"""

# Adjust these weights to fit your role/industry. They must sum to 1.0.
WEIGHT_SKILLS = 0.60
WEIGHT_EXPERIENCE = 0.25
WEIGHT_EDUCATION = 0.15


def compute_score(skills_result: dict, experience_result: dict, education_result: dict) -> dict:
    skills_pct = skills_result["match_pct"]
    experience_pct = experience_result["match_pct"]
    education_pct = education_result["match_pct"]

    overall = (
        skills_pct * WEIGHT_SKILLS
        + experience_pct * WEIGHT_EXPERIENCE
        + education_pct * WEIGHT_EDUCATION
    )
    overall = round(overall, 1)

    breakdown = {
        "overall_score": overall,
        "skills": {
            "weight": WEIGHT_SKILLS,
            "match_pct": skills_pct,
            "matched": skills_result["matched"],
            "missing": skills_result["missing"],
        },
        "experience": {
            "weight": WEIGHT_EXPERIENCE,
            "match_pct": experience_pct,
            "meets_requirement": experience_result["meets_requirement"],
        },
        "education": {
            "weight": WEIGHT_EDUCATION,
            "match_pct": education_pct,
            "meets_requirement": education_result["meets_requirement"],
        },
        "explanation": _build_explanation(skills_result, experience_result, education_result),
    }

    return breakdown


def _build_explanation(skills_result, experience_result, education_result) -> str:
    parts = []
    parts.append(
        f"Matched {len(skills_result['matched'])} of "
        f"{len(skills_result['matched']) + len(skills_result['missing'])} required skills "
        f"({skills_result['match_pct']}%)."
    )
    if skills_result["missing"]:
        parts.append(f"Missing: {', '.join(skills_result['missing'])}.")
    parts.append(
        "Meets experience requirement." if experience_result["meets_requirement"]
        else "Does not meet stated experience requirement."
    )
    parts.append(
        "Meets education requirement." if education_result["meets_requirement"]
        else "Does not meet stated education requirement."
    )
    return " ".join(parts)


def score_band(overall_score: float) -> str:
    """
    Human-readable band for quick scanning in the results table.
    These are advisory labels, NOT auto-decisions -- every candidate
    still requires human review per the system's workflow rules.
    """
    if overall_score >= 75:
        return "Strong match"
    elif overall_score >= 50:
        return "Possible match"
    else:
        return "Weak match"
