def get_suggestions(score, contact, text, ai_data=None):

    tips = []

    # If AI data has custom suggestions, use them
    if ai_data and "suggestions" in ai_data:
        for tip in ai_data["suggestions"]:
            clean_tip = tip.strip()
            if clean_tip:
                # Add prefix bullet if not already present
                if not clean_tip.startswith("🔹") and not clean_tip.startswith("•"):
                    clean_tip = f"🔹 {clean_tip}"
                tips.append(clean_tip)

    # GitHub check (always check layout/contact completeness)
    if contact["github"] == "Not Found" and not any("github" in t.lower() for t in tips):
        tips.append("🔹 Add your GitHub profile link.")

    # LinkedIn check
    if contact["linkedin"] == "Not Found" and not any("linkedin" in t.lower() for t in tips):
        tips.append("🔹 Add your LinkedIn profile link.")

    # Fallback to basic heuristics if no AI suggestions were found
    if len(tips) <= 2:  # which means only GitHub/LinkedIn might be added
        text = text.lower()

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