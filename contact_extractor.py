"""Contact information extractor.

Bugs fixed (Phase 1):
  P1-5 — GitHub regex had two identical patterns in an if/else block, meaning
          the else branch could never fire (it matched the same things as Case 1).
          All GitHub URLs are now normalized to https://github.com/<username>
          via a single unified regex + a plain-text "github: username" fallback.

  Also:  LinkedIn URLs are normalized to https://linkedin.com/in/<id>.
"""

from __future__ import annotations

import re


def extract_contact(text: str, ai_data: dict | None = None) -> dict[str, str]:
    """Extract contact details from resume text.

    AI-sourced values are used when available; regex-based extraction is
    applied as a fallback for any field the AI did not populate.

    Args:
        text:    Full plain-text resume content.
        ai_data: Optional dict returned by the local AI service. If it contains
                 a ``contact`` sub-dict those values take priority.

    Returns:
        A dict with keys: email, phone, linkedin, github.
        Missing fields carry the sentinel ``"Not Found"``.
    """
    ai_contact: dict[str, str] = {}
    if isinstance(ai_data, dict) and "contact" in ai_data:
        ai_contact = ai_data["contact"] if isinstance(ai_data["contact"], dict) else {}

    return {
        "email":    _resolve("email",    ai_contact, text, _extract_email),
        "phone":    _resolve("phone",    ai_contact, text, _extract_phone),
        "linkedin": _resolve("linkedin", ai_contact, text, _extract_linkedin),
        "github":   _resolve("github",  ai_contact, text, _extract_github),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SENTINEL = "Not Found"


def _resolve(
    key: str,
    ai_contact: dict[str, str],
    text: str,
    fallback_fn,
) -> str:
    """Return AI value if usable, otherwise run the regex fallback."""
    ai_val = ai_contact.get(key, _SENTINEL)
    if ai_val and ai_val.strip() and ai_val.strip() not in (_SENTINEL, "Not found", ""):
        return ai_val.strip()
    return fallback_fn(text)


def _extract_email(text: str) -> str:
    match = re.search(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        text,
        re.IGNORECASE,
    )
    return match.group(0) if match else _SENTINEL


def _extract_phone(text: str) -> str:
    """Match common international and Indian phone number formats."""
    # Accepts: +1 (555) 123-4567, +91 9876543210, 9876543210, (0)20 7946 0958
    match = re.search(
        r"(\+?[\d\s\-().]{7,20}\d)",
        text,
    )
    if match:
        candidate = match.group(0).strip()
        # Require at least 7 consecutive digits to rule out date strings
        digits_only = re.sub(r"\D", "", candidate)
        if len(digits_only) >= 7:
            return candidate
    return _SENTINEL


def _extract_linkedin(text: str) -> str:
    """Return a normalized https LinkedIn profile URL."""
    match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9_\-]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"https://linkedin.com/in/{match.group(1)}"
    return _SENTINEL


def _extract_github(text: str) -> str:
    """Return a normalized https GitHub profile URL.

    P1-5 fix: previously the function had two identical regex branches in an
    if/else — the else was dead code.  Now a single pattern handles full URLs,
    and a separate plain-text fallback handles 'GitHub: username' style entries.
    """
    # --- Attempt 1: Full or partial URL (github.com/username) ---
    url_match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.\-]+)",
        text,
        re.IGNORECASE,
    )
    if url_match:
        username = url_match.group(1)
        # Exclude generic path segments that aren't usernames
        if username.lower() not in ("features", "marketplace", "explore", "topics"):
            return f"https://github.com/{username}"

    # --- Attempt 2: Plain-text format e.g. "GitHub: koushik52" or "Github - koushik52" ---
    # Requires an explicit separator (colon or dash) to avoid matching arbitrary
    # words that happen to follow "github" in normal prose sentences.
    plain_match = re.search(
        r"github\s*[:\-]\s*([A-Za-z0-9_.\-]{2,39})\b",
        text,
        re.IGNORECASE,
    )
    if plain_match:
        username = plain_match.group(1)
        # Sanity-check: username shouldn't look like a sentence word
        if username.lower() not in ("profile", "url", "link", "page", "account", "repo"):
            return f"https://github.com/{username}"

    return _SENTINEL
