from llm_integration import extract_structured_data, generate_summary

def compute_scores(resume_text, jd_text):
    # Extract structured data with error handling
    resume_data = extract_structured_data(resume_text, extraction_type="resume")
    jd_data = extract_structured_data(jd_text, extraction_type="jd")
    
    # Check for extraction errors
    if "error" in resume_data or "error" in jd_data:
        return {
            "skill": 0,
            "skill_explanation": "Error in data extraction",
            "title": 0,
            "title_explanation": "Error in data extraction",
            "experience": 0,
            "experience_explanation": "Error in data extraction",
            "overall": 0,
            "overall_explanation": "Failed to extract necessary information"
        }
    
    skill_score = _compare_skills(resume_data.get("candidate_skills", []), jd_data.get("required_skills", []))
    title_score = _compare_titles(resume_data.get("job_title", ""), jd_data.get("job_title", ""))
    exp_score = _compare_experience(resume_data.get("years_of_experience", 0), jd_data.get("required_experience", 0))
    overall = 0.5 * skill_score + 0.3 * title_score + 0.2 * exp_score

    skill_explanation = f"Candidate has {len(set(resume_data.get('candidate_skills', [])).intersection(set(jd_data.get('required_skills', []))))} out of {len(set(jd_data.get('required_skills', [])))} required skills."
    title_explanation = f"Candidate's job title {'matches' if resume_data.get('job_title', '').lower() == jd_data.get('job_title', '').lower() else 'does not match'} the required job title."
    exp_explanation = f"Candidate has {resume_data.get('years_of_experience', 0)} years of experience compared to the required {jd_data.get('required_experience', 0)} years."

    scores = {
        "skill": round(skill_score, 2),
        "skill_explanation": skill_explanation,
        "title": round(title_score, 2),
        "title_explanation": title_explanation,
        "experience": round(exp_score, 2),
        "experience_explanation": exp_explanation,
        "overall": round(overall, 2),
        "overall_explanation": f"Based on weighted average: Skills ({skill_score * 0.5:.2f}), "
                             f"Job Title ({title_score * 0.3:.2f}), Experience ({exp_score * 0.2:.2f})"
    }
    return scores

def summarize_candidate(resume_text, jd_text, scores):
    # New detailed prompt with instructions for justification
    prompt = f"""You are an expert evaluator in candidate-job matching. Based on the following details, provide a detailed and justified explanation for the candidate's scores.
    
Candidate Resume:
{resume_text}

Job Description:
{jd_text}

Computed Scores:
- Skill Match Score: {scores.get('skill')}
- Job Title Relevance Score: {scores.get('title')}
- Experience Match Score: {scores.get('experience')}
- Overall Match Score: {scores.get('overall')}

Please justify each score:
1. Explain why the candidate's skills (or lack thereof) led to the Skill Match Score.
2. Explain how the candidate's job title aligns or does not align with the required job title.
3. Explain why the candidate's experience level is considered adequate or inadequate.
4. Summarize how the strengths and weaknesses combine to produce the overall score.

Provide your answer in detailed plain text."""
    return generate_summary(prompt)

def _compare_skills(resume_skills, jd_skills):
    match = len(set(resume_skills).intersection(set(jd_skills)))
    total = len(set(jd_skills)) or 1
    return match / total

def _compare_titles(resume_title, jd_title):
    if resume_title.lower() == jd_title.lower():
        return 1.0
    else:
        return 0.5

def _compare_experience(resume_exp, jd_exp):
    try:
        resume_exp = float(resume_exp)
        jd_exp = float(jd_exp)
    except (ValueError, TypeError):
        return 0.0
    if jd_exp == 0:
        return 1.0
    return min(resume_exp / jd_exp, 1.0)