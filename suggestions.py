"""Resume improvement suggestions generator.

Bug fixed (Phase 1):
  P1-6 — Suggestions compared contact values against `"Not Found"` (capital F)
          but `_coalesce()` in app.py normalises missing values to `"Not found"`
          (lowercase f), so the sentinel check never matched and suggestions for
          missing GitHub/LinkedIn/email/phone were silently suppressed.

          Fix: replaced all hardcoded sentinel literals with a helper function
          `_is_missing()` that normalises case before comparing.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Sentinel check helper (P1-6 fix)
# ---------------------------------------------------------------------------

def _is_missing(value: str | None) -> bool:
    """Return True if *value* represents a missing/not-found contact field.

    Handles all casing variants used across the codebase:
      - ``"Not Found"``   (contact_extractor.py output)
      - ``"Not found"``   (_coalesce() output in app.py)
      - empty string / None
    """
    if not value:
        return True
    return value.strip().lower() in ("not found", "not available", "none", "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_suggestions(
    resume_text: str,
    skills: list[str],
    contact: dict | None = None,
) -> list[str]:
    """Generate a list of actionable improvement suggestions for a resume.

    Args:
        resume_text: Extracted plain text of the resume.
        skills:      List of detected skill strings.
        contact:     Dict with keys ``email``, ``phone``, ``linkedin``,
                     ``github``. Non-dict values are handled gracefully.

    Returns:
        A flat list of suggestion strings (may be empty if the resume looks
        complete).
    """
    tips: list[str] = []

    # Normalise contact to dict (guards against accidental list/None)
    if not isinstance(contact, dict):
        contact = {}

    text_lower = (resume_text or "").lower()

    # -----------------------------------------------------------------------
    # Contact completeness
    # -----------------------------------------------------------------------
    if _is_missing(contact.get("email")):
        tips.append(
            "🔹 Missing email address — ensure your primary contact email is "
            "clearly visible at the top of the resume."
        )

    if _is_missing(contact.get("phone")):
        tips.append(
            "🔹 Missing phone number — add a preferred contact number so "
            "recruiters can reach you for interviews."
        )

    if _is_missing(contact.get("linkedin")):
        tips.append(
            "🔹 No LinkedIn URL detected — include your LinkedIn profile link "
            "to help recruiters view your full professional network."
        )

    if _is_missing(contact.get("github")):
        tips.append(
            "🔹 No GitHub link found — add your GitHub profile to showcase "
            "your project repositories and contributions."
        )

    # -----------------------------------------------------------------------
    # Resume structure
    # -----------------------------------------------------------------------
    if "education" not in text_lower:
        tips.append(
            "🔹 Add a dedicated 'Education' section with your degree, "
            "institution name, and expected/completed graduation year."
        )

    if "experience" not in text_lower and "work" not in text_lower and "internship" not in text_lower:
        tips.append(
            "🔹 Add a structured 'Professional Experience' or 'Work History' "
            "section — even internship or freelance work counts."
        )

    if "project" not in text_lower:
        tips.append(
            "🔹 Consider adding a 'Projects' section to demonstrate practical "
            "application of your skills with concrete outcomes."
        )

    # -----------------------------------------------------------------------
    # Skills density
    # -----------------------------------------------------------------------
    if len(skills) < 5:
        tips.append(
            "🔹 Expand your skills section — list more technical tools, "
            "programming languages, frameworks, or domain competencies. "
            "Aim for at least 8–10 relevant skills."
        )

    # -----------------------------------------------------------------------
    # Impact language
    # -----------------------------------------------------------------------
    action_verbs = [
        "developed", "built", "designed", "led", "improved",
        "reduced", "increased", "deployed", "optimised", "automated",
    ]
    if not any(verb in text_lower for verb in action_verbs):
        tips.append(
            "🔹 Use strong action verbs in bullet points "
            "(e.g. 'Developed', 'Reduced', 'Led') and quantify achievements "
            "where possible (e.g. 'Improved load time by 30%')."
        )

    return tips