# 🤖 AI Resume Analyzer & ATS Checker

An intelligent Resume Analyzer built using **Python** and **Streamlit** that helps job seekers evaluate their resumes, calculate an ATS (Applicant Tracking System) score, compare resumes with job descriptions, detect skills, identify missing skills, and receive personalized improvement suggestions.

---

## 🚀 Features

* ✅ ATS Score Calculation
* ✅ Resume Parsing from PDF
* ✅ Contact Information Extraction

  * Email Detection
  * Phone Number Detection
  * LinkedIn Profile Detection
  * GitHub Profile Detection
* ✅ Automatic Skill Detection
* ✅ Job Description Matching
* ✅ Matched Skills Identification
* ✅ Missing Skills Identification
* ✅ Resume Improvement Suggestions
* ✅ Resume Summary Generation
* ✅ Clean and Interactive Streamlit Interface

---

## 🛠️ Technologies Used

* **Python 3**
* **Streamlit**
* **Regular Expressions (re)**
* **PDF Text Extraction**
* **Git & GitHub**
* **VS Code**

### Python Modules

* streamlit
* PyPDF2 (or equivalent PDF parser)
* re
* os
* json

---

## 📂 Project Structure

```text
AI-Resume-Analyzer/
│── app.py
│── ats_score.py
│── contact_extractor.py
│── jd_matcher.py
│── resume_parser.py
│── skill_compare.py
│── skill_matcher.py
│── skills_db.py
│── suggestions.py
│── requirements.txt
│── README.md
```

---

## ⚙️ How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/Sangu-dev/AI-Resume-Analyzer.git
```

### 2. Open the project folder

```bash
cd AI-Resume-Analyzer
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit application

```bash
streamlit run app.py
```

### 5. Open the application

The app will open in your browser at:

```text
http://localhost:8501
```

---

## 📖 How It Works

1. Upload your resume in PDF format.
2. The application extracts text and contact details.
3. It calculates an ATS score based on resume content.
4. It detects technical skills from the resume.
5. Paste a job description to compare with your resume.
6. The app displays:

   * Job Match Score
   * Matched Skills
   * Missing Skills
   * Resume Improvement Suggestions

---

## 🎯 Use Cases

* Students applying for internships
* Fresh graduates preparing resumes
* Job seekers optimizing ATS scores
* Professionals comparing resumes with job descriptions

---

## 🔮 Future Enhancements

* AI-powered resume rewriting
* Multi-language resume support
* Resume ranking using machine learning
* Cover letter generation
* Interview question recommendations
* Resume keyword optimization
* Cloud deployment with authentication

---

## 👨‍💻 Author

**Sangamesh Ragam**

* GitHub: https://github.com/Sangu-dev
* LinkedIn: https://www.linkedin.com/in/sangamesh-ragam

---

## ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub and sharing it with others.
