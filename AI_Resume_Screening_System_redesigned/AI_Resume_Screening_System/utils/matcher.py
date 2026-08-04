"""
matcher.py
----------
Compares extracted candidate signals against the job's stated
requirements. Pure, transparent arithmetic -- no ML black box -- so
every match percentage can be explained to a candidate or auditor.
"""


def match_skills(candidate_skills: set, required_skills: set) -> dict:
    """
    Compare candidate skills to required skills.
    Returns matched skills, missing skills, and match percentage.
    """
    required_skills = {s.strip().lower() for s in required_skills if s.strip()}
    candidate_skills = {s.strip().lower() for s in candidate_skills}

    if not required_skills:
        return {"matched": [], "missing": [], "match_pct": 0.0}

    matched = required_skills & candidate_skills
    missing = required_skills - candidate_skills
    match_pct = round((len(matched) / len(required_skills)) * 100, 1)

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "match_pct": match_pct,
    }


def match_experience(candidate_years: int, required_years: int) -> dict:
    """
    Compare candidate's years of experience against the requirement.
    Capped at 100% -- more experience than required doesn't inflate
    the score further, which avoids a bias toward over-qualification.
    """
    if required_years <= 0:
        return {"match_pct": 100.0, "meets_requirement": True}

    match_pct = round(min(candidate_years / required_years, 1.0) * 100, 1)
    return {
        "match_pct": match_pct,
        "meets_requirement": candidate_years >= required_years,
    }


def match_education(candidate_level_score: int, required_level_score: int) -> dict:
    """
    Compare candidate's detected education level against the
    requirement. Capped at 100%.
    """
    if required_level_score <= 0:
        return {"match_pct": 100.0, "meets_requirement": True}

    match_pct = round(min(candidate_level_score / required_level_score, 1.0) * 100, 1)
    return {
        "match_pct": match_pct,
        "meets_requirement": candidate_level_score >= required_level_score,
    }
