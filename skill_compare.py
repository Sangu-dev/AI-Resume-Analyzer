from skill_matcher import find_skills

def compare_skills(resume_text, jd_text, ai_match_data=None):
    if ai_match_data and "matched_skills" in ai_match_data and "missing_skills" in ai_match_data:
        matched = sorted(list(set([s.strip().title() for s in ai_match_data["matched_skills"] if s.strip()])))
        missing = sorted(list(set([s.strip().title() for s in ai_match_data["missing_skills"] if s.strip()])))
        return matched, missing

    resume_skills = set(find_skills(resume_text))
    jd_skills = set(find_skills(jd_text))

    matched = sorted(list(resume_skills.intersection(jd_skills)))
    missing = sorted(list(jd_skills - resume_skills))

    return matched, missing