import streamlit as st
import hashlib

from resume_parser import extract_text
from skill_matcher import find_skills
from ats_score import ats_score
from contact_extractor import extract_contact
from jd_matcher import match_resume
from suggestions import get_suggestions
from skill_compare import compare_skills
import local_ai_service

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# Ollama Local LLM Check
# -----------------------------
ollama_active = local_ai_service.is_ollama_running()
installed_models = []
if ollama_active:
    installed_models = local_ai_service.get_local_models()

# -----------------------------
# Sidebar Configurations
# -----------------------------
st.sidebar.title("🤖 AI Resume Analyzer")

st.sidebar.markdown("### ⚙️ AI Engine Status")
if ollama_active:
    st.sidebar.success("🟢 Connected to Ollama")
    if installed_models:
        selected_model = st.sidebar.selectbox(
            "Select LLM Model",
            options=installed_models,
            index=0
        )
        use_ai = st.sidebar.checkbox("Enable AI Features", value=True)
    else:
        st.sidebar.warning("⚠️ No local models found.")
        st.sidebar.info("Run `ollama pull gemma3:1b` or `ollama pull llama3.2` in your terminal to install a model.")
        selected_model = None
        use_ai = False
else:
    st.sidebar.error("🔴 Ollama Offline")
    st.sidebar.info("""
    To enable local AI features:
    1. Install [Ollama](https://ollama.com).
    2. Run it on your machine.
    3. Run `ollama pull gemma3:1b` or `ollama pull llama3.2`.
    4. Refresh this page.
    """)
    selected_model = None
    use_ai = False

st.sidebar.divider()
st.sidebar.info("""
This tool helps you:
- ✅ Calculate ATS Score
- ✅ Detect Skills & Extract Contact Details
- ✅ Match Resume against Job Descriptions
- ✅ Find Missing Skills
- ✅ Get AI-Powered Suggestions
""")

# -----------------------------
# Main Header
# -----------------------------
st.title("🤖 Local AI Resume Analyzer & ATS Checker")

st.markdown("""
Analyze your resume locally and securely using Open Source LLMs (no data leaves your machine).
""")

if use_ai and selected_model:
    st.info(f"✨ running in **AI Mode** using local model `{selected_model}`")
else:
    st.warning("⚠️ running in **Basic Mode** (No local LLM active. Running standard static analysis rules)")

st.divider()

# -----------------------------
# Upload Resume & Job Description
# -----------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    uploaded = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

with col_right:
    jd = st.text_area(
        "Paste Job Description (Optional)",
        height=100,
        placeholder="Paste the target job description here to compare skill sets and check match suitability..."
    )

# -----------------------------
# Session State Caching
# -----------------------------
# Reset cache if a new file is uploaded or model changes
if uploaded:
    file_bytes = uploaded.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    
    if "current_file_hash" not in st.session_state or st.session_state.current_file_hash != file_hash:
        st.session_state.current_file_hash = file_hash
        st.session_state.ai_data = None
        st.session_state.ai_match_data = None
        st.session_state.last_jd_hash = ""
        st.session_state.resume_text = None

    # Cache text extraction
    if "resume_text" not in st.session_state or st.session_state.resume_text is None:
        st.session_state.resume_text = extract_text(uploaded)
    
    text = st.session_state.resume_text

    # Run AI Analysis if enabled and not already cached
    ai_data = None
    if use_ai and selected_model:
        if st.session_state.ai_data is None:
            with st.spinner(f"🤖 AI is analyzing resume structure & extracting details using {selected_model}..."):
                st.session_state.ai_data = local_ai_service.analyze_resume_local(text, selected_model)
        ai_data = st.session_state.ai_data

    # Extract Contact Details
    contact = extract_contact(text, ai_data=ai_data)

    # Detect Skills
    skills = find_skills(text, ai_data=ai_data)

    # Calculate ATS Score
    score = ats_score(text, skills, ai_data=ai_data)

    # Process Job Description Match
    ai_match_data = None
    if jd.strip() != "":
        jd_hash = hashlib.md5(jd.strip().encode()).hexdigest()
        
        if use_ai and selected_model:
            if st.session_state.ai_match_data is None or st.session_state.last_jd_hash != jd_hash:
                with st.spinner(f"🎯 AI is matching your profile with the job description..."):
                    st.session_state.ai_match_data = local_ai_service.match_jd_local(text, jd.strip(), selected_model)
                    st.session_state.last_jd_hash = jd_hash
            ai_match_data = st.session_state.ai_match_data

    # -----------------------------
    # Display Dashboard
    # -----------------------------
    st.success("✅ Resume processed successfully!")

    if ai_data and ai_data.get("candidate_name") and ai_data["candidate_name"] != "Not Found":
        st.subheader(f"👤 Candidate: {ai_data['candidate_name']}")

    # Columns for Layout
    d_col1, d_col2 = st.columns([1, 1])

    with d_col1:
        # ATS Score Widget
        st.subheader("📊 ATS Score")
        st.metric(label="ATS Score", value=f"{score}/100")
        st.progress(score / 100)

        if score >= 90:
            st.success("🟢 Excellent Resume structure & completeness")
        elif score >= 75:
            st.info("🔵 Good Resume - minor enhancements suggested")
        elif score >= 50:
            st.warning("🟡 Average Resume - needs missing content/structure revisions")
        else:
            st.error("🔴 Needs Improvement - layout or critical details missing")

    with d_col2:
        # Contact Details Widget
        st.subheader("📞 Contact Details")
        st.write("**📧 Email:**", contact["email"])
        st.write("**📱 Phone:**", contact["phone"])
        st.write("**🔗 LinkedIn:**", contact["linkedin"])
        st.write("**💻 GitHub:**", contact["github"])

    st.divider()

    # AI Summary
    if ai_data and ai_data.get("summary"):
        st.subheader("📋 Professional Summary (AI Generated)")
        st.info(ai_data["summary"])
        st.divider()

    # Detected Skills
    st.subheader("🛠️ Detected Skills")
    col1, col2 = st.columns(2)
    for i, skill in enumerate(skills):
        if i % 2 == 0:
            col1.success(skill)
        else:
            col2.success(skill)

    # Job Description Match
    if jd.strip() != "":
        st.divider()
        st.subheader("🎯 Job Match Analysis")
        
        match = match_resume(text, jd.strip(), ai_match_data=ai_match_data)
        
        m_col1, m_col2 = st.columns([1, 2])
        
        with m_col1:
            st.markdown("**Job Match Score:**")
            st.metric(label="Match Rate", value=f"{match}%")
            st.progress(min(int(match), 100))
        
        with m_col2:
            if ai_match_data and ai_match_data.get("reasoning"):
                st.markdown("**Match Fit Analysis:**")
                st.write(ai_match_data["reasoning"])
        
        matched_skills, missing_skills = compare_skills(text, jd.strip(), ai_match_data=ai_match_data)
        
        sc_col1, sc_col2 = st.columns(2)
        
        with sc_col1:
            st.subheader("✅ Matched Skills")
            if matched_skills:
                for skill in matched_skills:
                    st.success(skill)
            else:
                st.write("*No exact matching skills detected.*")
                
        with sc_col2:
            st.subheader("❌ Missing Skills")
            if missing_skills:
                for skill in missing_skills:
                    st.error(skill)
            else:
                st.write("*No critical missing skills detected! Great job.*")

    # Suggestions Widget
    st.divider()
    st.subheader("💡 Suggestions to Improve Resume")
    
    tips = get_suggestions(score, contact, text, ai_data=ai_data)
    
    if len(tips) == 0:
        st.success("Excellent! No major suggestions.")
    else:
        # Merge target suggestions from job match
        if ai_match_data and ai_match_data.get("customized_suggestions"):
            st.markdown("**Role-Specific Optimization Suggestions:**")
            for tip in ai_match_data["customized_suggestions"]:
                st.write(f"👉 {tip}")
            st.markdown("**General Resume Suggestions:**")
            
        for tip in tips:
            st.write(tip)

    # -----------------------------
    # Create Downloadable Report
    # -----------------------------
    report = f"""==================================================
AI RESUME ANALYZER REPORT
==================================================
Candidate: {ai_data.get('candidate_name', 'Not Extracted') if ai_data else 'Not Extracted'}
ATS Score: {score}/100
Mode: {"Local AI Mode (" + selected_model + ")" if (use_ai and selected_model) else "Basic Rule-Based Mode"}

CONTACT DETAILS:
- Email: {contact['email']}
- Phone: {contact['phone']}
- LinkedIn: {contact['linkedin']}
- GitHub: {contact['github']}

PROFESSIONAL SUMMARY:
{ai_data.get('summary', 'Not available (Run in AI mode to generate).') if ai_data else 'Not available (Run in AI mode to generate).'}

DETECTED SKILLS:
{", ".join(skills)}

"""
    if jd.strip() != "":
        report += f"""--------------------------------------------------
JOB DESCRIPTION MATCH ANALYSIS:
- Match Percentage: {match}%
"""
        if ai_match_data and ai_match_data.get("reasoning"):
            report += f"- Fit Analysis: {ai_match_data['reasoning']}\n"
            
        report += f"""
- Matched Skills: {', '.join(matched_skills)}
- Missing Skills: {', '.join(missing_skills)}
"""
        if ai_match_data and ai_match_data.get("customized_suggestions"):
            report += "\nROLE-SPECIFIC OPTIMIZATION RECOMMENDATIONS:\n"
            for tip in ai_match_data["customized_suggestions"]:
                report += f"- {tip}\n"

    report += "\n--------------------------------------------------\nRESUME IMPROVEMENT SUGGESTIONS:\n"
    for tip in tips:
        report += f"- {tip.replace('🔹 ', '')}\n"

    st.markdown("### 📥 Download Your Report")
    st.download_button(
        "Download Analysis Report",
        report,
        "resume_analysis_report.txt"
    )

st.markdown("---")
st.markdown(
    "<center>Made with ❤️ using Streamlit & Local Ollama</center>",
    unsafe_allow_html=True
)