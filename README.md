# 🤖 Local AI Resume Analyzer & ATS Checker

Hey there! 👋 Tired of sending your resume into the black hole of recruiter systems? This tool helps you check your resume's ATS score and optimize it against a job description—**completely offline and privately** on your own computer. 

No data leaves your machine. No cloud subscriptions. Just you, your code, and your local AI.

---

## 🚀 How to Get Running in 2 Minutes

### 1. Grab the Requirements
Install the Python packages:
```bash
pip install -r requirements.txt
```

### 2. Set Up Your Local Brain (Ollama)
We use the lightweight **Gemma 3 (1B)** model to do the thinking.
1. Download and run [Ollama](https://ollama.com).
2. Run this in your terminal to download the model:
   ```bash
   ollama pull gemma3:1b
   ```

### 3. Launch the App!
Run this command:
```bash
streamlit run app.py
```
Open the link that pops up in your browser (usually `http://localhost:8501`) and start analyzing!

---

## 💡 What it Does
* 📊 **ATS Score**: Rates how ATS-friendly your resume format is.
* 📞 **Contact Checker**: Verifies your email, phone, and profile links.
* 🛠️ **Skill Detective**: Automatically extracts your technical and soft skills.
* 🎯 **Job Matcher**: Paste a job description to instantly see missing skills and get matching scores.
* 📝 **AI Feedback & Summary**: Generates a professional summary and actionable tips to improve your resume.

---

## 📁 What's inside the Project?
* `app.py` - The user interface and dashboard.
* `local_ai_service.py` - The connector that talks to Ollama.
* `resume_parser.py` - Reads and extracts text from your PDF.
* Helper modules (`ats_score.py`, `contact_extractor.py`, `skill_compare.py`, `skill_matcher.py`, `suggestions.py`) for extraction and scoring.

---
Made with ❤️, Python, and local LLMs. Go get that job! 🚀
