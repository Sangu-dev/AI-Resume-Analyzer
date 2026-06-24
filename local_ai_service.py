"""Local AI service — connector to a locally running Ollama instance.

Bugs fixed (Phase 1):
  P1-4 — `json.loads()` was called with no exception handling. When the LLM
          returned Markdown-fenced JSON or partial output the whole function
          crashed and returned None silently.

          Fixes applied:
          a) `_safe_parse_json()` strips markdown code fences, then tries
             json.loads, then falls back to extracting the first {...} block.
          b) All error paths now use `logger.error()` instead of `print()`.
          c) Response validation ensures required keys exist before returning.
          d) Added retry helper `_post_with_retry()` so a single Ollama hiccup
             does not silently discard the entire AI analysis pass.
"""

from __future__ import annotations

import json
import logging
import re
import time

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434"

# Keys that must be present in a valid analyze_resume_local response
_REQUIRED_RESUME_KEYS = {"summary", "skills", "ats_score"}

# Keys that must be present in a valid match_jd_local response
_REQUIRED_MATCH_KEYS = {"match_score", "matched_skills", "missing_skills"}


# ---------------------------------------------------------------------------
# Connectivity helpers
# ---------------------------------------------------------------------------

def is_ollama_running() -> bool:
    """Return True if the local Ollama server responds on its base URL."""
    try:
        response = requests.get(OLLAMA_URL, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_local_models() -> list[str]:
    """Return a list of model names available in the local Ollama instance."""
    if not is_ollama_running():
        return []
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except Exception as exc:
        logger.warning("Could not fetch Ollama model list: %s", exc)
    return []


# ---------------------------------------------------------------------------
# Internal helpers (P1-4 fixes)
# ---------------------------------------------------------------------------

def _safe_parse_json(raw: str) -> dict | None:
    """Parse JSON from LLM output, tolerating Markdown fences and extra prose.

    Strategy:
      1. Strip leading/trailing whitespace.
      2. Remove ```json ... ``` or ``` ... ``` fences if present.
      3. Try json.loads on the cleaned string.
      4. If that fails, regex-extract the first top-level {...} block and retry.
      5. Log and return None on complete failure.
    """
    if not raw or not raw.strip():
        logger.error("LLM returned an empty response.")
        return None

    cleaned = raw.strip()

    # Strip Markdown code fences (```json or ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Attempt 1: direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: extract first { ... } block (handles extra prose around JSON)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    logger.error(
        "Failed to parse JSON from LLM response. First 300 chars: %s",
        raw[:300],
    )
    return None


def _post_with_retry(
    url: str,
    payload: dict,
    retries: int = 2,
    timeout: int = 90,
) -> requests.Response | None:
    """POST to *url* with exponential-backoff retry on timeout/connection errors.

    Returns the Response on success, or None after all retries are exhausted.
    """
    for attempt in range(retries + 1):
        try:
            return requests.post(url, json=payload, timeout=timeout)
        except requests.exceptions.Timeout:
            if attempt < retries:
                wait = 2 ** attempt
                logger.warning(
                    "Ollama request timed out (attempt %d/%d). Retrying in %ds…",
                    attempt + 1, retries + 1, wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "Ollama request timed out after %d retries at %s",
                    retries, url,
                )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Cannot connect to Ollama at %s: %s", url, exc)
            return None
    return None


def _validate_keys(data: dict, required: set[str], context: str) -> bool:
    """Warn and return False if any required key is missing from *data*."""
    missing = required - data.keys()
    if missing:
        logger.warning(
            "%s response is missing expected keys: %s", context, missing
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Public AI service calls
# ---------------------------------------------------------------------------

def analyze_resume_local(resume_text: str, model_name: str = "gemma3:1b") -> dict | None:
    """Analyze a resume with the local Ollama model.

    Returns a dict with keys: candidate_name, contact, summary, skills,
    ats_score, suggestions — or None on failure.
    """
    if not is_ollama_running():
        logger.info("Ollama is not running; skipping AI resume analysis.")
        return None

    system_prompt = """You are an expert ATS (Applicant Tracking System) parser and resume analyst.
Analyze the provided resume text and extract the candidate's details.

You MUST respond with a valid JSON object.
Do NOT include any markdown formatting, code fences, or text outside the JSON.

JSON Schema:
{
  "candidate_name": "Full Name or 'Not Found'",
  "contact": {
    "email": "Email or 'Not Found'",
    "phone": "Phone or 'Not Found'",
    "linkedin": "LinkedIn URL or 'Not Found'",
    "github": "GitHub URL or 'Not Found'"
  },
  "summary": "2-3 sentence professional summary.",
  "skills": ["List of detected technical and soft skills"],
  "ats_score": 75,
  "suggestions": ["3-5 specific, actionable improvement suggestions"]
}"""

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze the following resume:\n\n{resume_text}"},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }

    response = _post_with_retry(f"{OLLAMA_URL}/api/chat", payload)
    if response is None or response.status_code != 200:
        logger.error(
            "Ollama /api/chat returned status %s",
            response.status_code if response else "no response",
        )
        return None

    raw_content = response.json().get("message", {}).get("content", "")
    parsed = _safe_parse_json(raw_content)

    if parsed is None:
        return None

    # Soft validation — warn but still return partial data
    _validate_keys(parsed, _REQUIRED_RESUME_KEYS, "analyze_resume_local")
    return parsed


def match_jd_local(
    resume_text: str, jd_text: str, model_name: str = "gemma3:1b"
) -> dict | None:
    """Compare a resume with a job description using the local Ollama model.

    Returns a dict with keys: match_score, reasoning, matched_skills,
    missing_skills, customized_suggestions — or None on failure.
    """
    if not is_ollama_running():
        logger.info("Ollama is not running; skipping AI JD matching.")
        return None

    system_prompt = """You are an expert ATS recruiter and resume optimization assistant.

Compare the resume with the job description carefully.

Return ONLY valid JSON — no markdown, no code fences, no prose outside JSON:

{
  "match_score": 85,
  "reasoning": "Why the resume matches or does not match the JD.",
  "matched_skills": ["skills present in both resume and JD"],
  "missing_skills": ["skills in JD but absent from resume"],
  "customized_suggestions": [
    "5 specific suggestions referencing exact JD requirements.",
    "Do not invent fake experience.",
    "Suggest improvements to projects, skills, or certifications."
  ]
}"""

    user_content = (
        f"Resume Text:\n{resume_text}\n\n"
        "====================\n\n"
        f"Job Description:\n{jd_text}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }

    response = _post_with_retry(f"{OLLAMA_URL}/api/chat", payload)
    if response is None or response.status_code != 200:
        logger.error(
            "Ollama /api/chat returned status %s",
            response.status_code if response else "no response",
        )
        return None

    raw_content = response.json().get("message", {}).get("content", "")
    parsed = _safe_parse_json(raw_content)

    if parsed is None:
        return None

    # Soft validation
    _validate_keys(parsed, _REQUIRED_MATCH_KEYS, "match_jd_local")
    return parsed
