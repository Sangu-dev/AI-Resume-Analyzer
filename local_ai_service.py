import requests
import json
import re

OLLAMA_URL = "http://localhost:11434"

def is_ollama_running():
    """Check if the local Ollama server is running."""
    try:
        response = requests.get(OLLAMA_URL, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_local_models():
    """Retrieve the list of installed models from local Ollama."""
    if not is_ollama_running():
        return []
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
    except Exception:
        pass
    return []

def analyze_resume_local(resume_text, model_name="gemma3:1b"):
    """
    Use local Ollama to parse the resume text and return structured JSON containing:
    - candidate_name: String
    - contact: dict (email, phone, linkedin, github)
    - summary: String
    - skills: list of Strings
    - ats_score: Int (0-100)
    - suggestions: list of Strings
    """
    if not is_ollama_running():
        return None

    system_prompt = """
    You are an expert ATS (Applicant Tracking System) parser and resume analyst.
    Analyze the provided resume text and extract the candidate's details.
    
    You MUST respond with a valid JSON object matching the following structure. Do NOT include any markdown formatting, wrappers, or text outside the JSON object.
    
    JSON Schema:
    {
      "candidate_name": "Full Name of Candidate or 'Not Found'",
      "contact": {
        "email": "Email address or 'Not Found'",
        "phone": "Phone number or 'Not Found'",
        "linkedin": "LinkedIn profile URL or 'Not Found'",
        "github": "GitHub profile URL or 'Not Found'"
      },
      "summary": "A 2-3 sentence professional summary summarizing their experience and profile.",
      "skills": ["List of all detected technical, soft, and tool-based skills, normalized and capitalized nicely (e.g. Python, SQL, Project Management)"],
      "ats_score": 75, // Integer from 0 to 100 assessing layout structure, skill diversity, impact of bullet points, and profile completeness.
      "suggestions": ["List of 3-5 specific, actionable suggestions to improve the resume (e.g. 'Add quantifiable achievements in your projects section', 'Mention cloud platforms if applicable')"]
    }
    """

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze the following resume:\n\n{resume_text}"}
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        if response.status_code == 200:
            result_json = response.json()
            message_content = result_json.get("message", {}).get("content", "")
            
            # Parse the content into a dict
            parsed_data = json.loads(message_content)
            return parsed_data
    except Exception as e:
        print(f"Error in analyze_resume_local: {e}")
    return None

def match_jd_local(resume_text, jd_text, model_name="gemma3:1b"):
    """
    Use local Ollama to match the resume text with the job description.
    Returns structured JSON:
    - match_score: Int (0-100)
    - reasoning: String
    - matched_skills: list of Strings
    - missing_skills: list of Strings
    - customized_suggestions: list of Strings
    """
    if not is_ollama_running():
        return None

    system_prompt = """
    You are an expert recruiter and ATS resume matcher.
    Analyze the provided resume text against the Job Description (JD).
    
    You MUST respond with a valid JSON object matching the following structure. Do NOT include any markdown formatting, wrappers, or text outside the JSON object.
    
    JSON Schema:
    {
      "match_score": 85, // Integer from 0 to 100 indicating semantic match percentage.
      "reasoning": "A concise explanation of why the candidate is or isn't a good match for the role.",
      "matched_skills": ["Skills from the resume that align with the requirements of the job description"],
      "missing_skills": ["Key skills, tools, or requirements in the job description that are NOT found or implied in the resume"],
      "customized_suggestions": ["Actionable suggestions to customize this resume specifically for this job description (e.g. 'Highlight your experience with GCP under the Senior Engineer role')"]
    }
    """

    user_content = f"""
    Resume Text:
    {resume_text}
    
    ====================
    
    Job Description:
    {jd_text}
    """

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
        if response.status_code == 200:
            result_json = response.json()
            message_content = result_json.get("message", {}).get("content", "")
            
            # Parse the content into a dict
            parsed_data = json.loads(message_content)
            return parsed_data
    except Exception as e:
        print(f"Error in match_jd_local: {e}")
    return None
