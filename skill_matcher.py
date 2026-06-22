from skills_db import SKILLS

def find_skills(text, ai_data=None):
    if ai_data and "skills" in ai_data:
        # Normalize and return skills from AI
        ai_skills = [skill.strip().title() for skill in ai_data["skills"] if skill.strip()]
        return sorted(list(set(ai_skills)))

    # Fallback to hardcoded list
    text = text.lower()

    found = []

    for skill in SKILLS:
        if skill.lower() in text:
            found.append(skill.title())

    return sorted(list(set(found)))