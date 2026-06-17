def get_suggestions(score, contact, text):

    tips = []

    text = text.lower()

    # GitHub
    if contact["github"] == "Not Found":
        tips.append("🔹 Add your GitHub profile link.")

    # LinkedIn
    if contact["linkedin"] == "Not Found":
        tips.append("🔹 Add your LinkedIn profile link.")

    # Internship / Work Experience
    internship_keywords = [
        "internship",
        "intern",
        "work experience",
        "professional experience"
    ]

    found = False

    for keyword in internship_keywords:
        if keyword in text:
            found = True
            break

    if not found:
        tips.append("🔹 Consider adding internships or relevant work experience.")

    # Certifications
    if "certification" not in text and "certificate" not in text:
        tips.append("🔹 Consider adding certifications.")

    # Projects
    if "projects" not in text and "project" not in text:
        tips.append("🔹 Add academic or personal projects.")

    return tips