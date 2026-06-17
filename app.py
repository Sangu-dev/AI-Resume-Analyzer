import streamlit as st

from resume_parser import extract_text
from skill_matcher import find_skills
from ats_score import ats_score
from contact_extractor import extract_contact
from jd_matcher import match_resume
from suggestions import get_suggestions
from skill_compare import compare_skills

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# -----------------------------
# Page Configuration
# -----------------------------

st.sidebar.title("📄 AI Resume Analyzer")
st.sidebar.info("""
This tool helps you:
- ✅ Calculate ATS Score
- ✅ Detect Skills
- ✅ Compare with Job Description
- ✅ Find Missing Skills
- ✅ Get Resume Improvement Tips
""")

st.title("🤖 AI Resume Analyzer & ATS Checker")

st.markdown("""
Upload your resume and compare it with a job description.

### Features
- 📊 ATS Score
- 🎯 Job Match Score
- 🛠️ Detected Skills
- ❌ Missing Skills
- 💡 Resume Improvement Suggestions
""")

st.divider()

# -----------------------------
# Upload Resume
# -----------------------------
uploaded = st.file_uploader(
    "Upload Resume (PDF)",
    type=["pdf"]
)

# -----------------------------
# Job Description Input
# -----------------------------
jd = st.text_area(
    "Paste Job Description (Optional)"
)

# -----------------------------
# Process Resume
# -----------------------------
if uploaded:

    st.success("✅ Resume uploaded successfully!")

    # Extract Resume Text
    text = extract_text(uploaded)

    # Detect Skills
    skills = find_skills(text)

    # ATS Score
    score = ats_score(text, skills)

    # Contact Details
    contact = extract_contact(text)

    # -----------------------------
    # ATS Score
    # -----------------------------
    st.subheader("📊 ATS Score")
    st.metric(label="Score", value=f"{score}/100")
    st.progress(score / 100)

    if score >= 90:
        st.success("🟢 Excellent Resume")
    elif score >= 75:
        st.info("🔵 Good Resume")
    elif score >= 50:
        st.warning("🟡 Average Resume")
    else:
        st.error("🔴 Needs Improvement")

    # -----------------------------
    # Contact Details
    # -----------------------------
    st.subheader("📞 Contact Details")

    st.write("**📧 Email:**", contact["email"])
    st.write("**📱 Phone:**", contact["phone"])
    st.write("**🔗 LinkedIn:**", contact["linkedin"])
    st.write("**💻 GitHub:**", contact["github"])
    
    st.subheader("📋 Resume Summary")

    st.info(f"""
    **Total Skills Detected:** {len(skills)}

    ✅ Email: {"Found" if contact["email"] != "Not Found" else "Missing"}

    ✅ Phone: {"Found" if contact["phone"] != "Not Found" else "Missing"}

    ✅ LinkedIn: {"Found" if contact["linkedin"] != "Not Found" else "Missing"}

    ✅ GitHub: {"Found" if contact["github"] != "Not Found" else "Missing"}
    """)

    # -----------------------------
    # Skills
    # -----------------------------
    st.subheader("🛠️ Detected Skills")

    col1, col2 = st.columns(2)

    for i, skill in enumerate(skills):
        if i % 2 == 0:
            with col1:
                st.success(skill)
        else:
            with col2:
                st.success(skill)

    # -----------------------------
    # Job Match
    # -----------------------------
    if jd.strip() != "":

        match = match_resume(text, jd)

        st.subheader("🎯 Job Match Score")

        st.progress(min(int(match), 100))

        st.success(f"Resume matches **{match}%** with the Job Description.")

        matched, missing = compare_skills(text, jd)

        st.subheader("✅ Matched Skills")

        col1, col2 = st.columns(2)

        for i, skill in enumerate(matched):
            if i % 2 == 0:
                col1.success(skill)
            else:
                col2.success(skill)

        st.subheader("❌ Missing Skills")

        if missing:
            col1, col2 = st.columns(2)

        for i, skill in enumerate(missing):
            if i % 2 == 0:
                col1.error(skill)
            else:
                col2.error(skill)

    # -----------------------------
    # Suggestions
    # -----------------------------
    tips = get_suggestions(score, contact, text)

    st.subheader("💡 Suggestions to Improve Resume")

    if len(tips) == 0:
        st.success("Excellent! No major suggestions.")
    else:
        for tip in tips:
            st.write("•", tip)
    
    # -----------------------------
    # Create Report
    # -----------------------------
    report = f"""
    AI Resume Analyzer Report

    ATS Score: {score}/100

    Email: {contact['email']}
    Phone: {contact['phone']}
    LinkedIn: {contact['linkedin']}
    GitHub: {contact['github']}

    Detected Skills:
    {", ".join(skills)}

    Job Match Score:
    {match if jd.strip() else "Not Available"}%

    Resume Suggestions:
        """

    for tip in tips:
        report += f"\n- {tip}"

    # -----------------------------
    # Download Button
    # -----------------------------
    st.markdown("### 📥 Download Your Report")
    st.download_button(
        "Download Analysis Report",
        report,
        "resume_report.txt"
    )


    st.markdown("---")
    st.markdown(
        "<center>Made with ❤️ using Python & Streamlit</center>",
        unsafe_allow_html=True
    )