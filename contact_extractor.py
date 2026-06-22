import re

def extract_contact(text, ai_data=None):
    # If AI data is provided, use it as primary source
    ai_contact = {}
    if ai_data and "contact" in ai_data:
        ai_contact = ai_data["contact"]

    # -----------------------------
    # Extract Email
    # -----------------------------
    email = ai_contact.get("email", "Not Found")
    if email == "Not Found" or not email:
        email_match = re.search(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text,
            re.IGNORECASE
        )
        email = email_match.group(0) if email_match else "Not Found"

    # -----------------------------
    # Extract Phone Number
    # -----------------------------
    phone = ai_contact.get("phone", "Not Found")
    if phone == "Not Found" or not phone:
        phone_match = re.search(
            r"(\+?\d{1,3}[- ]?)?[6-9]\d{9}",
            text
        )
        phone = phone_match.group(0) if phone_match else "Not Found"

    # -----------------------------
    # Extract LinkedIn
    # -----------------------------
    linkedin = ai_contact.get("linkedin", "Not Found")
    if linkedin == "Not Found" or not linkedin:
        linkedin_match = re.search(
            r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9_/\-]+",
            text,
            re.IGNORECASE
        )
        if linkedin_match:
            linkedin = linkedin_match.group(0)

    # -----------------------------
    # Extract GitHub
    # -----------------------------
    github = ai_contact.get("github", "Not Found")
    if github == "Not Found" or not github:
        # Case 1: Full GitHub URL
        github_match = re.search(
            r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_.\-]+",
            text,
            re.IGNORECASE
        )

        if github_match:
            github = github_match.group(0)
        else:
            # Case 2: Formats like "Github ykoushik52"
            github_match = re.search(
                r"github\s*[:\-]?\s*([A-Za-z0-9_.\-]+)",
                text,
                re.IGNORECASE
            )

            if github_match:
                github = "http://github.com/" + github_match.group(1)

    # -----------------------------
    # Return Contact Details
    # -----------------------------
    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github
    }