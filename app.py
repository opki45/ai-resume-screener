import streamlit as st
import matplotlib.pyplot as plt
import string

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


st.set_page_config(page_title="AI Resume Screener", layout="centered")

st.title("AI Resume Screener")
st.write("Upload your CV and a job description to see how well they match.")


cv_file = st.file_uploader("Upload your CV as a .txt file", type=["txt"])
job_file = st.file_uploader("Upload the job description as a .txt file", type=["txt"])

TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql",
    "html", "css", "react", "node.js", "node", "express", "django",
    "flask", "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn",
    "sklearn", "machine learning", "deep learning", "data analysis",
    "data visualisation", "data visualization", "git", "github",
    "mysql", "postgresql", "mongodb", "api", "rest api", "aws",
    "azure", "docker", "linux", "excel", "power bi", "tableau",
    "communication", "teamwork", "problem solving", "agile"
]


def read_file(uploaded_file):
    return uploaded_file.read().decode("utf-8")

def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text

def find_skills(text, skills_list):
    found_skills = []

    for skill in skills_list:
        if skill.lower() in text:
            found_skills.append(skill)

    return sorted(set(found_skills))


if cv_file is not None and job_file is not None:
    cv_text = read_file(cv_file)
    job_text = read_file(job_file)

    st.success("CV and job description uploaded successfully.")

    documents = [cv_text, job_text]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    match_percentage = round(similarity_score * 100, 2)

    clean_cv = clean_text(cv_text)
    clean_job = clean_text(job_text)

    cv_skills = find_skills(clean_cv, TECH_SKILLS)
    job_skills = find_skills(clean_job, TECH_SKILLS)

    matched_skills = sorted(set(cv_skills).intersection(set(job_skills)))
    missing_skills = sorted(set(job_skills).difference(set(cv_skills)))

    if len(job_skills) > 0:
        skills_match_percentage = round((len(matched_skills) / len(job_skills)) * 100, 2)
    else:
        skills_match_percentage = 0
    
    st.subheader("Overall CV Match")
    
    col1, col2 = st.columns(2)
    col1.metric("Keyword Similarity Score", f"{match_percentage}%")
    col2.metric("Skills Match Score", f"{skills_match_percentage}%")

    if skills_match_percentage >= 70:
        rating = "Strong CV Match"
        feedback = "Your CV matches many of the key skills required for this role."
    elif skills_match_percentage >= 40:
        rating = "Moderate CV Match"
        feedback = "Your CV matches some key skills, but there are areas you could tailor more closely."
    else:
        rating = "Weak CV Match"
        feedback = "Your CV is missing several key skills from the job description."

    st.write(f"### {rating}")
    st.write(feedback)


    st.subheader("Skills Analysis")

    col1, col2, col3 = st.columns(3)

    col1.metric("Skills Found in CV", len(cv_skills))
    col2.metric("Skills Required by Job", len(job_skills))
    col3.metric("Missing Skills", len(missing_skills))

    st.write("#### Matched Skills")
    if matched_skills:
        st.write(", ".join(matched_skills))
    else:
        st.write("No major matching skills found.")

    st.write("#### Missing Skills")
    if missing_skills:
        st.write(", ".join(missing_skills))
    else:
        st.write("No major missing skills detected from the skill list.")

    st.subheader("CV Fit Visualisation")

    labels = ["Matched Skills", "Missing Skills"]
    values = [len(matched_skills), len(missing_skills)]

    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title("Matched vs Missing Skills")
    ax.set_ylabel("Number of Skills")

    st.pyplot(fig)

    st.subheader("Improvement Suggestions")

    if missing_skills:
        st.write("Consider adding evidence of these skills if you genuinely have experience with them:")
        for skill in missing_skills:
            st.write(f"- {skill}")
    else:
        st.write("Your CV already covers the main skills detected in the job description.")

    st.info(
        "Tip: Do not add skills you do not actually have. Instead, tailor your project descriptions to clearly show the relevant skills you already used."
    )