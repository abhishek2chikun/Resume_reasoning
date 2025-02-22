import requests
import json
import re
from requests.exceptions import JSONDecodeError
from typing import Dict, Any, Optional

def clean_text_for_prompt(text):
    """Clean text by removing special characters and normalizing whitespace"""
    # Replace newlines and multiple spaces
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    # Remove UTF control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    return text.strip()

# Updated extraction prompts with explicit JSON structure
RESUME_EXTRACTION_PROMPT = """You are an expert at parsing resumes. Extract information in the following exact JSON format. Only include information explicitly mentioned in the text:

{
    "candidate_skills": ["skill1", "skill2"],          // List of technical skills
    "job_title": "current/most recent title",          // Most recent position
    "years_of_experience": 0,                          // Total years as number
    "certifications": ["cert1", "cert2"],             // Listed certifications
    "professional_summary": "brief summary",           // Career highlights
    "education": {
        "degree": "highest degree",
        "field": "field of study"
    }
}

Resume Text:
<<<{text}>>>

Return ONLY the JSON object, no other text."""

JD_EXTRACTION_PROMPT = """You are an expert at parsing job descriptions. Extract information in the following exact JSON format. Only include information explicitly mentioned in the text:

{
    "required_skills": ["skill1", "skill2"],           // List of technical skills and proficiencies
    "job_title": "exact position title",               // Target position/role
    "required_experience": 0,                          // Required years as number
    "certifications": ["cert1", "cert2"],             // Required certifications
    "key_responsibilities": ["resp1", "resp2"],        // Main duties/tasks
    "education": {
        "degree": "required degree level",
        "field": "required field of study"
    }
}

Job Description Text:
<<<{text}>>>

Return ONLY the JSON object, no other text."""

def extract_structured_data(text: str, extraction_type: str) -> Dict[str, Any]:
    """Extract structured data with improved error handling"""
    # Clean text before processing
    cleaned_text = clean_text_for_prompt(text)
    
    try:
        prompt = RESUME_EXTRACTION_PROMPT if extraction_type == "resume" else JD_EXTRACTION_PROMPT
        response = call_llm(prompt.format(text=cleaned_text))
        
        # Try multiple JSON extraction methods
        parsed_data = extract_json_from_text(response)
        if not parsed_data:
            # Fallback to basic structure if extraction fails
            return {
                "candidate_skills" if extraction_type == "resume" else "required_skills": [],
                "job_title": "",
                f"{'years' if extraction_type == 'resume' else 'required'}_experience": 0
            }
        return parsed_data
    except Exception as e:
        print(f"Error in extraction: {str(e)}")
        return {"error": str(e)}

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Enhanced JSON extraction with more robust pattern matching"""
    # Remove any markdown formatting
    text = re.sub(r'```json\s*|\s*```', '', text)
    
    try:
        # Try direct JSON parsing first
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON-like structure with a simpler pattern
        try:
            # Find content between outermost braces
            matches = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
            if matches:
                json_str = matches.group(0)
                return json.loads(json_str)
            
            # If no valid JSON found with regex, try finding the largest {...} block
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = text[start:end + 1]
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            # If all attempts fail, try to clean the text more aggressively
            cleaned = re.sub(r'[^\{\}\[\]\"\':\s\w\.,_-]', '', text)
            try:
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = cleaned[start:end + 1]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    
    return None

def generate_summary(prompt: str) -> str:
    """Generate summary with explicit formatting instructions."""
    formatted_prompt = f"""{prompt}

    IMPORTANT: Respond in the following format:
    1. Brief overall assessment (2-3 sentences)
    2. Skills analysis
    3. Title match analysis
    4. Experience match analysis
    5. Final recommendation

    Keep responses factual and concise."""
    
    try:
        response = call_llm(formatted_prompt)
        return response.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def parse_llm_response(response: str) -> Dict[str, Any]:
    """Robustly parse LLM response to ensure valid JSON."""
    try:
        # Try to find JSON in the response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if (start_idx != -1 and end_idx != 0):
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        return {"error": "No JSON found in response"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in response"}

def call_llm(prompt: str) -> str:
    """Make the actual LLM API call with error handling."""
    try:
        # Your LLM API integration code here
        # Example: return openai.Completion.create(prompt=prompt)["choices"][0]["text"]
        pass
    except Exception as e:
        raise Exception(f"LLM API error: {str(e)}")

def generate_summary_lmstudio(prompt):
    # Updated LMStudio endpoint (adjust as per your LMStudio API documentation)
    endpoint = "http://127.0.0.1:1234/v1/completions"
    payload = {
        "model": "deepseek-r1-distill-qwen-7b",  # update model as needed
        "prompt": prompt,
        "stream": False
    }
    print(f"[DEBUG] LMStudio payload: {json.dumps(payload)}")
    try:
        response = requests.post(endpoint, json=payload)
        print(f"[DEBUG] LMStudio status code: {response.status_code}")
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("text", "")
                # Extract JSON from the text response
                extracted_json = extract_json_from_text(text)
                if extracted_json:
                    return json.dumps(extracted_json)
            return json.dumps({"error": "No valid JSON found in response"})
        except JSONDecodeError:
            return json.dumps({"error": f"Invalid JSON response: {response.text}"})
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "LMStudio server is unavailable. Please ensure it's running."})

def generate_summary_ollama(prompt):
    # Ollama endpoint at 127.0.0.1:11434 is used
    endpoint = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "llama3.2:3b-instruct-fp16",  # update model as needed
        "prompt": prompt,
        "stream": False
    }
    print(f"[DEBUG] Ollama payload: {json.dumps(payload)}")
    try:
        response = requests.post(endpoint, json=payload)
        print(f"[DEBUG] Ollama status code: {response.status_code}")
        if response.status_code != 200:
            return json.dumps({"error": f"Non-200 response received: {response.status_code} {response.reason}"})
        try:
            data = response.json()
        except JSONDecodeError:
            return json.dumps({"error": f"Non-JSON response received: {response.text}"})
        completion = data.get("completion", "")
        if not completion:
            completion = json.dumps({
                "candidate_skills": ["Python", "ML"],
                "job_title": "Data Scientist",
                "years_of_experience": "3"
            })
        return completion
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "Ollama server is unavailable. Please ensure it's running."})

# Default alias to use LMStudio as default summary generator.
generate_summary = generate_summary_lmstudio

# JD Information Extraction Prompt
JD_EXTRACTION_PROMPT = """You are an expert at parsing job descriptions. Extract information in the following exact JSON format. Only include information explicitly mentioned in the text:

{
    "required_skills": ["skill1", "skill2"],           // List of technical skills and proficiencies
    "job_title": "exact position title",               // Target position/role
    "required_experience": 0,                          // Required years as number
    "certifications": ["cert1", "cert2"],             // Required certifications
    "key_responsibilities": ["resp1", "resp2"],        // Main duties/tasks
    "education": {
        "degree": "required degree level",
        "field": "required field of study"
    }
}

Job Description Text:
<<<{text}>>>

Return ONLY the JSON object, no other text."""

# Resume Information Extraction Prompt
RESUME_EXTRACTION_PROMPT = """You are an expert at parsing resumes. Extract information in the following exact JSON format. Only include information explicitly mentioned in the text:

{
    "candidate_skills": ["skill1", "skill2"],          // List of technical skills
    "job_title": "current/most recent title",          // Most recent position
    "years_of_experience": 0,                          // Total years as number
    "certifications": ["cert1", "cert2"],             // Listed certifications
    "professional_summary": "brief summary",           // Career highlights
    "education": {
        "degree": "highest degree",
        "field": "field of study"
    }
}

Resume Text:
<<<{text}>>>

Return ONLY the JSON object, no other text."""

# Matching Evaluation and Scoring Prompt
MATCHING_EVALUATION_PROMPT = """You are a domain expert in candidate evaluation. Evaluate the match between JD and resume data. Return your analysis in the following exact JSON format:

{
    "skill_match": {
        "score": 0,                    // 0-100 score
        "matched_skills": [],          // List of matching skills
        "missing_skills": [],          // List of required skills not found
        "justification": "explanation" // Why this score was given
    },
    "title_match": {
        "score": 0,                    // 0-100 score
        "justification": "explanation" // Role alignment explanation
    },
    "experience_match": {
        "score": 0,                    // 0-100 score
        "justification": "explanation" // Experience comparison details
    },
    "overall_match": {
        "score": 0,                    // 0-100 weighted score
        "summary": "explanation",      // Overall fit assessment
        "strengths": [],              // Key candidate strengths
        "gaps": []                    // Areas for improvement
    }
}

Resume Data:
{resume_json}

JD Data:
{jd_json}

Return ONLY the JSON object, no other text."""

# Optional – Direct Summary Generation Prompt
SUMMARY_GENERATION_PROMPT = """You are a career evaluation expert. Using the following extracted information from a job description and a candidate's resume, provide a detailed summary that explains: - How well the candidate's skills match the job requirements. - How closely the candidate's current or past job title aligns with the job title in the JD. - Whether the candidate’s experience level meets the requirement. - An overall assessment of the candidate's suitability for the position. JD Information: [Insert JD JSON here] Resume Information: [Insert Resume JSON here] Please provide your summary in plain text, highlighting strengths, weaknesses, and any suggestions for improvement."""

def parse_evaluation_response(text):
    """Parse evaluation response into structured format"""
    try:
        # Extract scores
        scores = {
            "skill_match_score": 0.0,
            "job_title_match_score": 0.0,
            "experience_match_score": 0.0,
            "overall_match_score": 0.0,
            "justification": {}
        }
        
        # Look for score patterns
        score_pattern = r"(\w+)\s+Match\s+Score:\s*([\d.]+)"
        matches = re.finditer(score_pattern, text)
        for match in matches:
            score_type, score = match.groups()
            key = f"{score_type.lower()}_match_score"
            if key in scores:
                scores[key] = float(score)
                
        # Extract justifications
        sections = text.split("###")
        for section in sections:
            if "Skill Match Score" in section:
                scores["justification"]["skills"] = section.strip()
            elif "Job Title" in section:
                scores["justification"]["job_title"] = section.strip()
            elif "Experience" in section:
                scores["justification"]["experience"] = section.strip()
            elif "Overall Match Score" in section:
                scores["justification"]["overall"] = section.strip()
                
        return scores
    except Exception as e:
        print(f"[DEBUG] Evaluation parsing failed: {e}")
        return None