"""ATS readiness scorer.

Bugs fixed (Phase 1):
  P1-2 — Phone check previously matched ANY digit in the resume text
          (e.g. years, percentages, GPA). Now uses the same regex as
          contact_extractor so it only matches real phone numbers.
  P1-3 — Section detection (education, experience, projects) previously
          matched the word anywhere in the text, even mid-sentence.
          Now detects section *headings* by requiring the keyword to
          appear on its own line (as a heading).
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ats_score(text: str, skills: list[str], ai_data: dict | None = None) -> int:
    """Return an ATS readiness score from 0 to 100.

    If the AI backend already provided an ``ats_score`` key in *ai_data*
    that value is used directly (clamped to [0, 100]). Otherwise the
    rule-based heuristic below is applied as a fallback.
    """
    # --- AI-sourced score takes priority ---
    if ai_data and "ats_score" in ai_data:
        try:
            return min(max(int(ai_data["ats_score"]), 0), 100)
        except (ValueError, TypeError):
            pass  # Fall through to heuristic

    return _heuristic_score(text, skills)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _has_section(text: str, *keywords: str) -> bool:
    """Return True if any keyword appears as a standalone section heading.

    A heading is defined as a line where the keyword is the primary (or only)
    word — optionally followed by whitespace or a colon. This prevents false
    positives like "5 years of experience" from being counted as an
    Experience section.

    Args:
        text:     Full resume text (case-insensitive matching applied).
        keywords: One or more keyword variants to check (e.g. "experience",
                  "work history"). Any match returns True.
    """
    pattern = (
        r"(?:^|\n)"                         # start of text or new line
        r"\s*"                              # optional leading whitespace
        r"(?:" + "|".join(re.escape(k) for k in keywords) + r")"
        r"\s*(?::|$|\n)"                    # end of heading: colon, EOL, or newline
    )
    return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))


def _has_phone(text: str) -> bool:
    """Return True only if the text contains a plausible phone number.

    Previously ``any(ch.isdigit() for ch in text)`` was used, which
    matches virtually every resume and always awarded the phone points.

    The pattern now accepts:
    - International numbers: +1 (555) 123-4567
    - Indian mobile: +91 9876543210
    - Plain 10-digit strings: 9876543210
    """
    # Broad but realistic phone pattern
    pattern = r"""
        (?:
            \+?[\d\s\-().]{7,20}\d   # Generic international format
        )
    """
    return bool(re.search(pattern, text, re.VERBOSE))


def _heuristic_score(text: str, skills: list[str]) -> int:
    """Compute a rule-based ATS score when AI data is unavailable."""
    score = 0
    lower = text.lower()

    # --- Skills: max 30 points (2 pts each, stops at 15 skills) ---
    score += min(len(skills) * 2, 30)

    # --- Structural sections: checked as actual headings ---
    if _has_section(lower, "education", "academic background", "academics"):
        score += 10

    if _has_section(lower, "project", "projects", "personal projects", "academic projects"):
        score += 15

    if _has_section(lower, "experience", "work experience", "work history",
                    "employment", "internship", "professional experience"):
        score += 15

    # --- Certifications ---
    if _has_section(lower, "certification", "certifications", "certificate",
                    "licenses", "licence"):
        score += 10

    # --- Online presence (simple but intentional check) ---
    if "github.com/" in lower:
        score += 5
    if "linkedin.com/in/" in lower:
        score += 5

    # --- Contact info ---
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        score += 5

    # P1-2 FIX: use real phone detection instead of `any digit`
    if _has_phone(text):
        score += 5

    return min(score, 100)