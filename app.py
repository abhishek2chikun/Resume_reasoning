import streamlit as st
import os
from extraction import extract_text_from_file
from matching_engine import compute_scores, summarize_candidate

def single_resume_matching():
    st.title("Single Resume & JD Matching")
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
    jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx"])
    if st.button("Process"):
        if resume_file and jd_file:
            resume_text = extract_text_from_file(resume_file)
            jd_text = extract_text_from_file(jd_file)
            scores = compute_scores(resume_text, jd_text)
            summary = summarize_candidate(resume_text, jd_text, scores)
            
            # Display scores and explanations in expandable sections
            with st.expander("Skill Match Analysis"):
                st.write(f"Score: {scores['skill']}")
                st.write("Explanation:", scores['skill_explanation'])
            
            with st.expander("Job Title Relevance Analysis"):
                st.write(f"Score: {scores['title']}")
                st.write("Explanation:", scores['title_explanation'])
            
            with st.expander("Experience Match Analysis"):
                st.write(f"Score: {scores['experience']}")
                st.write("Explanation:", scores['experience_explanation'])
            
            st.write("Overall Match Score:", scores["overall"])
            st.write("Overall Analysis:", scores["overall_explanation"])
            st.write("Detailed Candidate Summary:", summary)
        else:
            st.write("Please upload both files to proceed.")

def multi_resume_ranking():
    st.title("Multiple Resumes & JD Ranking")
    jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx"])
    resume_files = st.file_uploader("Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True)
    if st.button("Rank Resumes"):
        if jd_file and resume_files:
            jd_text = extract_text_from_file(jd_file)
            all_scores = []
            for file in resume_files:
                resume_text = extract_text_from_file(file)
                scores = compute_scores(resume_text, jd_text)
                all_scores.append((file.name, scores["overall"], scores))
            ranked = sorted(all_scores, key=lambda x: x[1], reverse=True)
            
            for item in ranked:
                with st.expander(f"Resume: {item[0]} - Overall Score: {item[1]}"):
                    scores = item[2]
                    st.write("Skills Analysis:", scores['skill_explanation'])
                    st.write("Title Analysis:", scores['title_explanation'])
                    st.write("Experience Analysis:", scores['experience_explanation'])
                    st.write("Overall Analysis:", scores['overall_explanation'])
        else:
            st.write("Please upload one JD and multiple resumes.")

def main():
    page = st.sidebar.selectbox("Page", ["Single Resume Matching", "Multiple Resumes Ranking"])
    if page == "Single Resume Matching":
        single_resume_matching()
    else:
        multi_resume_ranking()

if __name__ == "__main__":
    main()