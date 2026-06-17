from skill_matcher import find_skills

def compare_skills(resume_text, jd_text):

    resume_skills = set(find_skills(resume_text))
    jd_skills = set(find_skills(jd_text))

    matched = sorted(list(resume_skills.intersection(jd_skills)))
    missing = sorted(list(jd_skills - resume_skills))

    return matched, missing