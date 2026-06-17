def ats_score(text, skills):

    score = 0
    text = text.lower()

    # Skills (maximum 30)
    score += min(len(skills) * 2, 30)

    # Education
    if "education" in text:
        score += 10

    # Projects
    if "project" in text:
        score += 15

    # Experience
    if "experience" in text or "internship" in text:
        score += 15

    # Certifications
    if "certification" in text or "certificate" in text:
        score += 10

    # GitHub
    if "github" in text:
        score += 5

    # LinkedIn
    if "linkedin" in text:
        score += 5

    # Email
    if "@" in text:
        score += 5

    # Phone
    if "+" in text or any(ch.isdigit() for ch in text):
        score += 5

    return min(score, 100)