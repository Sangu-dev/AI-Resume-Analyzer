from skill_matcher import find_skills

def match_resume(resume_text, jd_text):
    resume_skills = set(find_skills(resume_text))
    jd_skills = set(find_skills(jd_text))

    if len(jd_skills) == 0:
        return 0

    matched = resume_skills.intersection(jd_skills)

    score = (len(matched) / len(jd_skills)) * 100

    return round(score, 2)