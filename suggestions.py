def get_suggestions(resume_text, skills, contact=None):
    tips = []
    
    # CRASH PROTECTION: If contact is a list or something else, convert it safely
    if not isinstance(contact, dict):
        contact = {}
        
    # Lowercase the text for easy searching
    text_lower = resume_text.lower() if resume_text else ""

    # Check for GitHub link safely
    if contact.get("github") == "Not Found":
        tips.append("🔹 Add a link to your GitHub profile to showcase your project repositories.")

    # Check for LinkedIn link safely
    if contact.get("linkedin") == "Not Found":
        tips.append("🔹 Include your LinkedIn profile URL to help recruiters find your network.")

    # Check for standard contact fields safely
    if contact.get("email") == "Not Found":
        tips.append("🔹 Missing Email address: Ensure your primary contact email is visible at the top.")
        
    if contact.get("phone") == "Not Found":
        tips.append("🔹 Missing Phone number: Add a preferred contact number for interviews.")

    # Basic structural recommendations
    if "education" not in text_lower:
        tips.append("🔹 Include an explicit 'Education' section with your degree and graduation details.")
        
    if "experience" not in text_lower and "work" not in text_lower:
        tips.append("🔹 Add a structured 'Professional Experience' or 'Work History' section.")

    if len(skills) < 5:
        tips.append("🔹 Expand your skills section to include more technical tools, languages, or core competencies.")

    return tips