"""Resume Analyzer — Production-grade Streamlit application.

Provides ATS scoring, skill extraction, contact parsing, job-description
matching, and optional local-AI insights. Built for clarity, resilience,
and maintainability.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional

import streamlit as st

# --------------------------------------------------------------------------- #
#  Local module imports (fail fast with a clear message if anything is missing)
# --------------------------------------------------------------------------- #
try:
    from ats_score import ats_score
    from contact_extractor import extract_contact
    from jd_matcher import match_resume
    from resume_parser import extract_text
    from skill_compare import compare_skills
    from skill_matcher import find_skills
    from suggestions import get_suggestions
    import local_ai_service
except ImportError as exc:
    st.error(
        f"Missing local module dependency: **{exc.name}**. "
        "Please ensure all project modules are on PYTHONPATH and restart the app."
    )
    st.stop()

# --------------------------------------------------------------------------- #
#  Logging
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Constants
# --------------------------------------------------------------------------- #
APP_NAME = "Resume Analyzer"
APP_ICON = "📄"
SUPPORTED_TYPES = ["pdf", "txt"]
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# High-contrast palette (darker muted text for visibility)
COLOR_ACCENT = "#12715b"
COLOR_INK = "#18201d"
COLOR_MUTED = "#3d4f48"  # Darkened from #65726d for better readability
COLOR_TAG_BG = "#e1f3ed"
COLOR_TAG_BORDER = "#a8d5c5"
COLOR_TAG_TEXT = "#0d4f3f"

# --------------------------------------------------------------------------- #
#  Data models
# --------------------------------------------------------------------------- #
@dataclass
class ContactInfo:
    email: str = "Not found"
    phone: str = "Not found"
    linkedin: str = "Not found"
    github: str = "Not found"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, str]]) -> ContactInfo:
        if not isinstance(data, dict):
            return cls()
        return cls(
            email=_coalesce(data.get("email")),
            phone=_coalesce(data.get("phone")),
            linkedin=_coalesce(data.get("linkedin")),
            github=_coalesce(data.get("github")),
        )


@dataclass
class AnalysisResult:
    resume_text: str = ""
    skills: List[str] = field(default_factory=list)
    contact: ContactInfo = field(default_factory=ContactInfo)
    ats_score: int = 0
    suggestions: List[str] = field(default_factory=list)
    ai_summary: Optional[str] = None
    match_percentage: Optional[int] = None
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    ai_reasoning: Optional[str] = None
    ai_tailoring: List[str] = field(default_factory=list)
    error: Optional[str] = None


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #
def _coalesce(value: Optional[str], fallback: str = "Not found") -> str:
    """Return a cleaned string or a fallback."""
    return value if value and value.strip() and value != "Not Found" else fallback


def _compute_hash(content: bytes | str) -> str:
    """Stable MD5 hash for cache invalidation."""
    hasher = hashlib.md5()
    if isinstance(content, str):
        hasher.update(content.encode("utf-8"))
    else:
        hasher.update(content)
    return hasher.hexdigest()


def _clean_recommendation(text: str) -> str:
    """Normalize bullet characters and whitespace."""
    return text.strip().lstrip("-*• ").strip()


def _init_session_state() -> None:
    """Ensure every expected session key exists with a safe default."""
    defaults = {
        "analysis": None,
        "file_hash": None,
        "jd_hash": None,
        "selected_model": None,
        "use_ai": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --------------------------------------------------------------------------- #
#  Cached service layer  (expensive / deterministic work)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def _cached_extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extract text from uploaded file bytes."""
    try:
        return extract_text(io.BytesIO(file_bytes))
    except Exception as exc:
        logger.exception("Text extraction failed")
        raise RuntimeError(f"Could not extract text from {file_name}: {exc}") from exc


@st.cache_data(show_spinner=False)
def _cached_find_skills(resume_text: str) -> List[str]:
    try:
        return find_skills(resume_text) or []
    except Exception as exc:
        logger.exception("Skill extraction failed")
        return []


@st.cache_data(show_spinner=False)
def _cached_ats_score(
    resume_text: str, skills: List[str], ai_data: Optional[Dict[str, Any]]
) -> int:
    try:
        return ats_score(resume_text, skills, ai_data) or 0
    except Exception as exc:
        logger.exception("ATS scoring failed")
        return 0


@st.cache_data(show_spinner=False)
def _cached_get_suggestions(
    resume_text: str, skills: List[str], contact: Dict[str, str]
) -> List[str]:
    try:
        return get_suggestions(resume_text, skills, contact) or []
    except Exception as exc:
        logger.exception("Suggestion generation failed")
        return []


@st.cache_data(show_spinner=False)
def _cached_match_resume(
    resume_text: str, jd_text: str, ai_match_data: Optional[Dict[str, Any]]
) -> Optional[int]:
    try:
        return match_resume(resume_text, jd_text, ai_match_data)
    except Exception as exc:
        logger.exception("JD matching failed")
        return None


@st.cache_data(show_spinner=False)
def _cached_compare_skills(
    resume_text: str, jd_text: str, ai_match_data: Optional[Dict[str, Any]]
) -> tuple[List[str], List[str]]:
    try:
        matched, missing = compare_skills(resume_text, jd_text, ai_match_data)
        return matched or [], missing or []
    except Exception as exc:
        logger.exception("Skill comparison failed")
        return [], []


# --------------------------------------------------------------------------- #
#  AI service wrappers  (not cached — depends on external Ollama state)
# --------------------------------------------------------------------------- #
def _analyze_with_ai(resume_text: str, model: str) -> Optional[Dict[str, Any]]:
    try:
        with st.status("🧠 Generating AI resume feedback...", expanded=False) as status:
            result = local_ai_service.analyze_resume_local(resume_text, model)
            status.update(label="AI analysis complete", state="complete", expanded=False)
            return result
    except Exception as exc:
        logger.exception("Local AI resume analysis failed")
        st.toast(f"AI resume analysis failed: {exc}", icon="⚠️")
        return None


def _match_with_ai(
    resume_text: str, jd_text: str, model: str
) -> Optional[Dict[str, Any]]:
    try:
        with st.status("🧠 Comparing resume with target role...", expanded=False) as status:
            result = local_ai_service.match_jd_local(resume_text, jd_text, model)
            status.update(label="Role comparison complete", state="complete", expanded=False)
            return result
    except Exception as exc:
        logger.exception("Local AI JD matching failed")
        st.toast(f"AI role matching failed: {exc}", icon="⚠️")
        return None


# --------------------------------------------------------------------------- #
#  UI Components
# --------------------------------------------------------------------------- #
def _inject_styles() -> None:
    """Inject minimal, high-contrast custom CSS."""
    css = f"""
    <style>
    .hero-kicker {{
        color: {COLOR_ACCENT};
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }}
    .hero-subtitle {{
        color: {COLOR_MUTED};
        font-size: 1.1rem;
        line-height: 1.6;
        max-width: 720px;
    }}
    .tag-pill {{
        display: inline-block;
        background-color: {COLOR_TAG_BG};
        color: {COLOR_TAG_TEXT};
        border: 1px solid {COLOR_TAG_BORDER};
        border-radius: 999px;
        padding: 0.35rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem 0.25rem 0.25rem 0;
    }}
    .status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #eef3ef;
        border: 1px solid #dce4df;
        border-radius: 999px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 700;
        color: {COLOR_INK};
    }}
    .status-dot {{
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background: {COLOR_ACCENT};
    }}
    .status-dot.off {{
        background: #b45309;
    }}
    </style>
    """
    try:
        if hasattr(st, "html"):
            st.html(css)
        else:
            st.markdown(css, unsafe_allow_html=True)
    except Exception:
        pass  # Graceful degradation to default Streamlit theming


def _render_hero() -> None:
    st.markdown(
        '<p class="hero-kicker">ATS and Role Fit Workspace</p>',
        unsafe_allow_html=True,
    )
    st.title("Sharper resume feedback, without the clutter.")
    st.markdown(
        '<p class="hero-subtitle">Upload a resume, paste a target role when you have '
        "one, and get a focused read on ATS readiness, skills, contact quality, and "
        "gaps worth fixing first.</p>",
        unsafe_allow_html=True,
    )


def _render_empty_state() -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("**1. Upload**")
            st.caption("Add your resume in PDF or TXT format.")
    with c2:
        with st.container(border=True):
            st.markdown("**2. Compare**")
            st.caption("Paste a job description to unlock fit analysis.")
    with c3:
        with st.container(border=True):
            st.markdown("**3. Improve**")
            st.caption("Export a clean report with the key fixes.")


def _render_tags(items: List[str], empty_msg: str = "None detected") -> None:
    """Render skill tags as high-contrast pills."""
    clean_items = [str(i).strip() for i in items if str(i).strip()]
    if not clean_items:
        st.caption(empty_msg)
        return
    tags_html = "".join(f'<span class="tag-pill">{escape(i)}</span>' for i in clean_items)
    st.markdown(
        f'<div style="margin: 0.5rem 0 1rem;">{tags_html}</div>',
        unsafe_allow_html=True,
    )


def _render_contact_card(contact: ContactInfo) -> None:
    """Render contact info using native Streamlit components for perfect visibility."""
    with st.container(border=True):
        rows = [
            ("Email", contact.email),
            ("Phone", contact.phone),
            ("LinkedIn", contact.linkedin),
            ("GitHub", contact.github),
        ]
        for label, value in rows:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(value)


def _build_report(result: AnalysisResult) -> str:
    """Generate a clean Markdown report."""
    lines = [
        "# Resume Analysis Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Metrics",
        f"- **ATS Readiness:** {result.ats_score}/100",
        f"- **Skills Found:** {len(result.skills)}",
    ]
    if result.match_percentage is not None:
        lines.append(f"- **Role Match:** {result.match_percentage}%")

    lines.extend([
        "",
        "## Contact Information",
        f"- **Email:** {result.contact.email}",
        f"- **Phone:** {result.contact.phone}",
        f"- **LinkedIn:** {result.contact.linkedin}",
        f"- **GitHub:** {result.contact.github}",
        "",
        "## Professional Summary",
        result.ai_summary or "No AI summary available.",
        "",
        "## Skills Detected",
        ", ".join(result.skills) if result.skills else "None detected",
    ])

    if result.match_percentage is not None:
        lines.extend([
            "",
            "## Role Alignment",
            f"- **Matched Skills:** {', '.join(result.matched_skills) if result.matched_skills else 'None'}",
            f"- **Missing Skills:** {', '.join(result.missing_skills) if result.missing_skills else 'None'}",
        ])
        if result.ai_reasoning:
            lines.extend(["", "### AI Reasoning", result.ai_reasoning])
        if result.ai_tailoring:
            lines.extend([
                "",
                "### Tailoring Suggestions",
                *[f"- {_clean_recommendation(tip)}" for tip in result.ai_tailoring],
            ])

    lines.extend([
        "",
        "## Recommendations",
        *(
            [f"- {_clean_recommendation(tip)}" for tip in result.suggestions]
            if result.suggestions
            else ["No recommendations generated."]
        ),
    ])
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Main application
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_styles()
    _init_session_state()

    # ----------------------------------------------------------------------- #
    #  Sidebar
    # ----------------------------------------------------------------------- #
    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        st.caption("Private resume review with optional local AI.")

        # AI status probe
        try:
            ollama_active = local_ai_service.is_ollama_running()
            models = local_ai_service.get_local_models() if ollama_active else []
        except Exception as exc:
            logger.warning("Could not query Ollama status: %s", exc)
            ollama_active = False
            models = []

        dot_class = "" if ollama_active else " off"
        status_text = "Local AI online" if ollama_active else "Local AI offline"
        st.markdown(
            f"""
            <div class="status-pill">
                <span class="status-dot{dot_class}"></span>
                {status_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        selected_model: Optional[str] = None
        use_ai = False

        if ollama_active and models:
            selected_model = st.selectbox(
                "AI Model",
                options=models,
                index=0,
                help="Choose the local Ollama model for summaries and role reasoning.",
                key="selected_model",
            )
            use_ai = st.checkbox(
                "Enable deep insight analysis", value=True, key="use_ai"
            )
        elif ollama_active:
            st.warning("Ollama is running, but no models were found.")
        else:
            st.info("Start Ollama to enable AI summaries and richer role feedback.")

        st.divider()
        st.caption("Upload PDF or TXT resumes. Analysis runs locally.")

        if st.button("🔄 Reset Analysis", use_container_width=True):
            for key in ("analysis", "file_hash", "jd_hash"):
                st.session_state[key] = None
            st.rerun()

    # ----------------------------------------------------------------------- #
    #  Hero + Inputs
    # ----------------------------------------------------------------------- #
    _render_hero()
    st.divider()

    input_col, jd_col = st.columns([1, 1], gap="large")

    with input_col:
        st.markdown("### Resume")
        uploaded_file = st.file_uploader(
            "Upload resume",
            type=SUPPORTED_TYPES,
            label_visibility="collapsed",
            help=f"Supported formats: {', '.join(SUPPORTED_TYPES).upper()}. Max {MAX_FILE_SIZE_MB} MB.",
        )

        if uploaded_file is not None:
            if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                st.error(f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")
                st.stop()
            with st.container(border=True):
                st.success(f"✅ **{uploaded_file.name}** is loaded for review.")
        else:
            with st.container(border=True):
                st.info("Drop in a PDF or TXT resume to generate scores and recommendations.")

    with jd_col:
        st.markdown("### Target Role")
        jd_text = st.text_area(
            "Paste job description",
            height=188,
            label_visibility="collapsed",
            placeholder="Paste a job description to compare role fit, matched skills, and missing keywords.",
        )
        if jd_text.strip():
            st.caption("Role matching will be included in the analysis.")
        else:
            st.caption("Optional, but useful when tailoring a resume for a specific opening.")

    # ----------------------------------------------------------------------- #
    #  Empty state guard
    # ----------------------------------------------------------------------- #
    if uploaded_file is None:
        st.divider()
        _render_empty_state()
        st.stop()

    # ----------------------------------------------------------------------- #
    #  Analysis pipeline
    # ----------------------------------------------------------------------- #
    result = AnalysisResult()

    # File processing
    try:
        file_bytes = uploaded_file.getvalue()
        file_hash = _compute_hash(file_bytes)
    except Exception as exc:
        st.error(f"Failed to read uploaded file: {exc}")
        st.stop()

    # Determine if we need to re-run analysis
    current_jd_hash = _compute_hash(jd_text) if jd_text.strip() else None
    cached_analysis: Optional[AnalysisResult] = st.session_state.get("analysis")
    cached_file_hash = st.session_state.get("file_hash")
    cached_jd_hash = st.session_state.get("jd_hash")

    if (
        cached_analysis is None
        or cached_file_hash != file_hash
        or cached_jd_hash != current_jd_hash
    ):
        # New or changed inputs — run full analysis
        with st.spinner("Reading resume content..."):
            try:
                resume_text = _cached_extract_text(file_bytes, uploaded_file.name)
            except RuntimeError as exc:
                st.error(str(exc))
                st.stop()

        if not resume_text.strip():
            st.error(
                "Could not extract readable text from this resume. "
                "Try a text-based PDF or TXT file."
            )
            st.stop()

        result.resume_text = resume_text

        # Optional AI analysis
        ai_data: Optional[Dict[str, Any]] = None
        ai_match_data: Optional[Dict[str, Any]] = None

        if use_ai and selected_model:
            ai_data = _analyze_with_ai(resume_text, selected_model)
            if jd_text.strip():
                ai_match_data = _match_with_ai(resume_text, jd_text, selected_model)

        # Core analysis (cached where possible)
        with st.status("Running analysis...", expanded=False) as status:
            skills = _cached_find_skills(resume_text)
            contact_dict = extract_contact(resume_text, ai_data)
            contact = ContactInfo.from_dict(contact_dict)
            ats = _cached_ats_score(resume_text, skills, ai_data)
            suggestions = _cached_get_suggestions(
                resume_text, skills, contact_dict or {}
            )

            result.skills = skills
            result.contact = contact
            result.ats_score = ats
            result.suggestions = suggestions
            result.ai_summary = ai_data.get("summary") if ai_data else None

            # JD matching
            if jd_text.strip():
                match_pct = _cached_match_resume(resume_text, jd_text, ai_match_data)
                matched, missing = _cached_compare_skills(
                    resume_text, jd_text, ai_match_data
                )
                result.match_percentage = match_pct
                result.matched_skills = matched
                result.missing_skills = missing
                result.ai_reasoning = (
                    ai_match_data.get("reasoning") if ai_match_data else None
                )
                result.ai_tailoring = (
                    ai_match_data.get("customized_suggestions")
                    if ai_match_data
                    else []
                )

            status.update(label="Analysis complete", state="complete", expanded=False)

        # Persist in session state
        st.session_state.analysis = result
        st.session_state.file_hash = file_hash
        st.session_state.jd_hash = current_jd_hash
    else:
        result = cached_analysis

    # ----------------------------------------------------------------------- #
    #  Results display
    # ----------------------------------------------------------------------- #
    st.divider()
    st.markdown("## Snapshot")

    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.metric("ATS Readiness", f"{result.ats_score}/100")
    with m2:
        with st.container(border=True):
            match_display = (
                f"{result.match_percentage}%" if result.match_percentage is not None else "Not set"
            )
            st.metric("Role Match", match_display)
    with m3:
        with st.container(border=True):
            st.metric("Skills Found", str(len(result.skills)))

    st.divider()

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("## Profile")

        # Summary
        st.markdown("#### Summary")
        summary = (
            result.ai_summary
            or "Enable local AI in the sidebar to generate a tailored professional summary."
        )
        st.markdown(summary)

        # Skills
        st.markdown("#### Skills")
        _render_tags(
            sorted(set(result.skills)),
            "No known skills were detected from the current resume text.",
        )

        # Contact
        st.markdown("#### Contact")
        _render_contact_card(result.contact)

    with right_col:
        st.markdown("## Next Moves")

        if jd_text.strip():
            # Role alignment tabs
            st.markdown("#### Role Alignment")
            tab_match, tab_missing, tab_reasoning = st.tabs(
                ["✅ Matched", "⚠️ Gaps", "📝 Notes"]
            )

            with tab_match:
                _render_tags(
                    result.matched_skills,
                    "No direct overlap was detected for this role description.",
                )

            with tab_missing:
                if result.missing_skills:
                    _render_tags(result.missing_skills, "")
                else:
                    st.success("No obvious keyword gaps were detected.")

            with tab_reasoning:
                if result.ai_reasoning:
                    st.markdown(result.ai_reasoning)
                else:
                    st.caption("Enable local AI to see detailed role-fit reasoning.")

            # Tailoring suggestions
            if result.ai_tailoring:
                st.markdown("#### Tailoring Suggestions")
                for tip in result.ai_tailoring:
                    st.markdown(f"- {_clean_recommendation(tip)}")

            # General recommendations
            if result.suggestions:
                st.markdown("#### General Recommendations")
                for tip in result.suggestions:
                    st.markdown(f"- {_clean_recommendation(tip)}")
        else:
            st.markdown("#### Recommended Fixes")
            if result.suggestions:
                for tip in result.suggestions:
                    st.markdown(f"- {_clean_recommendation(tip)}")
            else:
                st.caption("No immediate fixes were generated for this resume.")

    # ----------------------------------------------------------------------- #
    #  Export
    # ----------------------------------------------------------------------- #
    st.divider()
    st.markdown("## Export")

    report_md = _build_report(result)
    col_dl, _ = st.columns([1, 3])
    with col_dl:
        st.download_button(
            label="📥 Download Report",
            data=report_md,
            file_name="resume_analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()