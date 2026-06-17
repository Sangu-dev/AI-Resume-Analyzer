from skills_db import SKILLS

def find_skills(text):
    text = text.lower()

    found = []

    for skill in SKILLS:
        if skill.lower() in text:
            found.append(skill.title())

    return sorted(list(set(found)))