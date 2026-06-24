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
# Page Configuration & Professional Branding
# -----------------------------
st.set_page_config(
    page_title="Professional Resume Suite",
    page_icon="👔",
    layout="wide"
)

# Custom minimalistic styling injection to polish native elements
st.markdown("""
    <style>
    /* Styling metric card backgrounds slightly for a container look */
    [data-testid="stMetricSimpleValue"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        padding: 15px 25px;
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    /* Smooth button layouts */
    .stButton>button {
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Background Configuration (Ollama Services)
# -----------------------------
ollama_active = local_ai_service.is_ollama_running()
installed_models = local_ai_service.get_local_models() if ollama_active else []

# Cleaned up Sidebar: Moving technical configs into a clean, collapsible section
with st.sidebar:
    st.title("Settings")
    st.caption("Configure optimization settings below.")
    
    with st.expander("🛠️ Advanced Engine Settings", expanded=False):
        if ollama_active:
            st.success("Connected securely to optimizer.")
            if installed_models:
                selected_model = st.selectbox(
                    "Analysis Engine Profile",
                    options=installed_models,
                    index=0
                )
                use_ai = st.checkbox("Enable Deep Insight Analysis", value=True)
            else:
                st.warning("No dynamic profiles found.")
                selected_model = None
                use_ai = False
        else:
            st.error("Offline intelligence service not running.")
            selected_model = None
            use_ai = False

# -----------------------------
# Header Section
# -----------------------------
st.title("Smart Resume Optimizer")
st.markdown("Enhance your professional presentation, match requirements, and optimize readability for enterprise systems instantly.")

# -----------------------------
# Main Application Content Tabs
# -----------------------------
# Replacing standard linear structures with interactive tabs for an organized view
tab1, tab2 = st.tabs(["📄 Document Optimization", "🎯 Targeted Role Matcher"])

with tab1:
    st.subheader("Upload and Audit")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF or TXT format)", 
        type=["pdf", "txt"],
        help="Your document remains private and is analyzed locally."
    )
    
    # Simple placeholder behavior to prevent full screen empty layout
    if not uploaded_file:
        st.info("Please upload your professional document above to view key metrics.")

with tab2:
    st.subheader("Role Alignment Tool")
    jd_text = st.text_area(
        "Paste target Job Description / Requirements:", 
        height=200, 
        placeholder="Paste the explicit job profile parameters here..."
    )

# -----------------------------
# Processing Engine Framework
# -----------------------------
if uploaded_file:
    # 1. Parse File Content safely
    with st.spinner("Analyzing document structure..."):
        file_bytes = uploaded_file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        uploaded_file.seek(0)
        
        resume_text = extract_text(uploaded_file)
        
    if not resume_text.strip():
        st.error("Unable to extract valid structural layout text from this file format.")
    else:
        # 2. Extract Data Points via Intelligence layer
        ai_data = None
        ai_match_data = None
        
        if use_ai and selected_model:
            # Setup session state caching safely against file hash modifications
            if "file_hash" not in st.session_state or st.session_state.file_hash != file_hash:
                with st.spinner("Generating professional summary and strategic feedback..."):
                    ai_data = local_ai_service.analyze_resume_local(resume_text, selected_model)
                    st.session_state.ai_data = ai_data
                    st.session_state.file_hash = file_hash
            else:
                ai_data = st.session_state.ai_data
                
            # Perform targeted role analysis if job profile data exists
            if jd_text.strip() != "":
                if "jd_hash" not in st.session_state or st.session_state.jd_hash != hashlib.md5(jd_text.encode()).hexdigest():
                    with st.spinner("Calculating role compatibility..."):
                        ai_match_data = local_ai_service.match_jd_local(resume_text, jd_text, selected_model)
                        st.session_state.ai_match_data = ai_match_data
                        st.session_state.jd_hash = hashlib.md5(jd_text.encode()).hexdigest()
                else:
                    ai_match_data = st.session_state.ai_match_data

        # 3. Base Extractors Fallback
        skills = find_skills(resume_text)
        contact = extract_contact(resume_text, ai_data)
        score = ats_score(resume_text, skills, ai_data)
        tips = get_suggestions(resume_text, skills, contact)
        
        # -----------------------------
        # Dashboard Analytics Interface
        # -----------------------------
        st.divider()
        st.subheader("Performance Indicators")
        
        # Clean corporate metric column split
        m_col1, m_col2, m_col3 = st.columns(3)
        
        with m_col1:
            st.metric(label="System Readability Score", value=f"{score}/100")
            
        with m_col2:
            if jd_text.strip() != "":
                match_pct = match_resume(resume_text, jd_text, ai_match_data)
                st.metric(label="Target Role Compatibility", value=f"{match_pct}%")
            else:
                st.metric(label="Target Role Compatibility", value="--", help="Provide a job description in Tab 2")
                
        with m_col3:
            st.metric(label="Identified Key Competencies", value=str(len(skills)))

        # -----------------------------
        # Detailed Insights View Splits
        # -----------------------------
        st.divider()
        col_left, col_right = st.columns([1, 1], gap="large")
        
        with col_left:
            st.markdown("### 👤 Profile Summary")
            summary_content = ai_data.get('summary', 'Summary optimization is running on base context mode.') if ai_data else 'Summary generation requires AI capabilities enabled.'
            st.write(summary_content)
            
            st.markdown("### 🛠️ Extracted Competencies")
            if skills:
                # Using modern pills formatting instead of custom code line text joins
                st.pills("Found Skills", options=sorted(list(set(skills))), label_visibility="collapsed")
            else:
                st.caption("No standard profile core competencies detected dynamically.")

            st.markdown("### 📞 Validated Contact Fields")
            c1, c2 = st.columns(2)
            with c1:
                email_val = contact.get('email', 'Not Found')
                if email_val != "Not Found":
                    st.markdown(f"**Email:** [{email_val}](mailto:{email_val})")
                else:
                    st.markdown("**Email:** *Not Found*")
                    
                st.markdown(f"**Phone:** {contact.get('phone', 'Not Found')}")
                
            with c2:
                li_val = contact.get('linkedin', 'Not Found')
                if li_val != "Not Found":
                    li_link = li_val if li_val.startswith("http") else f"https://{li_val}"
                    st.markdown(f"**LinkedIn:** [View Profile]({li_link})")
                else:
                    st.markdown("**LinkedIn:** *Not Found*")
                    
                gh_val = contact.get('github', 'Not Found')
                if gh_val != "Not Found":
                    gh_link = gh_val if gh_val.startswith("http") else f"https://github.com/{gh_val}"
                    st.markdown(f"**GitHub:** [View Repositories]({gh_link})")
                else:
                    st.markdown("**GitHub:** *Not Found*")

        with col_right:
            # Dynamic conditional matching content
            if jd_text.strip() != "":
                st.markdown("### 🎯 Role Gap Analysis")
                matched_skills, missing_skills = compare_skills(resume_text, jd_text, ai_match_data)
                
                tab_match, tab_missing = st.tabs(["✅ Matched Attributes", "⚠️ Development Gaps"])
                with tab_match:
                    if matched_skills:
                        st.pills("Matched", options=matched_skills, label_visibility="collapsed")
                    else:
                        st.caption("No direct matching overlap found for the specified role parameters.")
                with tab_missing:
                    if missing_skills:
                        st.pills("Missing", options=missing_skills, label_visibility="collapsed")
                    else:
                        st.caption("Exceptional! No clear keyword criteria profile gap observed.")

                if ai_match_data and ai_match_data.get("reasoning"):
                    st.markdown("**Strategic Compatibility Overview:**")
                    st.info(ai_match_data["reasoning"])
                    
                if ai_match_data and ai_match_data.get("customized_suggestions"):
                    st.markdown("**Role Optimization Adjustments:**")
                    for recommendation in ai_match_data["customized_suggestions"]:
                        st.markdown(f"• {recommendation}")
            else:
                st.markdown("### 📈 Quality Enhancement Actions")
                for optimization_tip in tips:
                    clean_tip = optimization_tip.replace('🔹 ', '')
                    st.markdown(f"• {clean_tip}")

        # -----------------------------
        # Export Actions
        # -----------------------------
        st.divider()
        st.markdown("### 📥 Document Audit Report")
        
        # Build beautiful structured clean text file compilation
        report = f"""COMPREHENSIVE RESUME OPTIMIZATION AUDIT
==================================================
METRICS OVERVIEW:
- System Readability Score: {score}/100
- Total Core Skills Parsed: {len(skills)}

CONTACT SUMMARY:
- Email: {contact.get('email', 'Not Found')}
- Phone: {contact.get('phone', 'Not Found')}
- LinkedIn: {contact.get('linkedin', 'Not Found')}
- GitHub: {contact.get('github', 'Not Found')}

PROFESSIONAL CONTEXT:
{summary_content}

CORE RECOGNIZED SKILLS:
{', '.join(skills)}
"""
        if jd_text.strip() != "":
            report += f"\n==================================================\nROLE MATCH AUDIT SCORE: {match_pct}%\n"
            if ai_match_data and ai_match_data.get("reasoning"):
                report += f"- Structural Analysis: {ai_match_data['reasoning']}\n"
            report += f"- Shared Skills: {', '.join(matched_skills)}\n- Target Profile Gaps: {', '.join(missing_skills)}\n"

        report += "\n==================================================\nACTIONABLE RECOMMENDATIONS:\n"
        for optimization_tip in tips:
            report += f"- {optimization_tip.replace('🔹 ', '')}\n"

        st.download_button(
            label="Download Complete Optimization Report",
            data=report,
            file_name="resume_optimization_report.txt",
            mime="text/plain"
        )