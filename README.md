# AI Resume Screener

An AI-powered resume screening tool that analyses how well a CV matches a job description using Natural Language Processing (NLP). Built to help university students and graduates optimise their CVs with data-driven insights and improve their chances of landing interviews.

---

## Overview

Recruiters often scan CVs in seconds, looking for specific skills and keywords. Many companies use Applicant Tracking Systems (ATS) to filter CVs automatically before a human even sees them. This project simulates that process by:

- Parsing your CV and job description (PDF, DOCX, or TXT)
- Calculating a composite match score across four weighted components
- Detecting matched and missing skills from a taxonomy of 80+ technologies
- Adjusting scoring weights based on whether the role is an internship, mid-level, or senior position
- Providing actionable feedback, interview prep questions, and a candidate summary

---

## Features

- **Composite Match Score** — weighted across skills, keyword similarity, experience, and education
- **Role-Level Detection** — automatically detects intern/graduate, mid-level, or senior roles and adjusts weights accordingly
- **Skills Gap Analysis** — matched vs missing skills displayed as colour-coded badges
- **80+ Skill Taxonomy** — covers languages, frameworks, cloud, DevOps, ML, and soft skills with synonym matching
- **CV Formatting Feedback** — checks word count, bullet points, key sections, and contact details
- **ATS Outcome Prediction** — tells you whether your CV is likely to pass automated screening
- **Candidate Summary** — plain-English paragraph summarising your application
- **Interview Preparation Questions** — generated from your specific skill gaps
- **Improvement Suggestions** — varied, actionable advice for each missing skill
- **CSV Export** — download your full screening report
- **PDF, DOCX, and TXT support** — no manual conversion needed

---

## Tech Stack

- **Python**
- **Streamlit** — interactive web app
- **scikit-learn** — TF-IDF vectorisation and cosine similarity
- **pdfplumber** — PDF text extraction
- **python-docx** — DOCX text extraction
- **matplotlib** — score visualisations
- **pytest** — unit tests

---

## How It Works

1. Upload your CV and a job description (PDF, DOCX, or TXT)
2. The role type is detected (intern / mid / senior) and weights are set accordingly
3. Text is cleaned and normalised — preserving skill names like C++, C#, and Node.js
4. Skills are extracted using word-boundary regex matching against an 80+ skill taxonomy
5. TF-IDF cosine similarity measures vocabulary alignment
6. Years of experience and education level are extracted and compared
7. A weighted composite score is calculated and displayed with per-component explanations
8. Interview questions, improvement suggestions, and a candidate summary are generated from the gaps

---

## Scoring Model

| Component | Intern/Grad | Mid-level | Senior |
|---|---|---|---|
| Skills match | 75% | 40% | 35% |
| Keyword similarity | 0% | 30% | 25% |
| Experience | 10% | 15% | 30% |
| Education | 15% | 15% | 10% |

Keyword similarity is zeroed for intern roles because a student CV naturally uses different vocabulary to a corporate JD — this is expected and should not penalise the candidate.

---

## Installation & Usage

**1. Clone the repository**
```bash
git clone https://github.com/opki45/ai-resume-screener.git
cd ai-resume-screener
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
streamlit run app.py
```

---

## Project Structure

```
ai-resume-screener/
│
├── app.py                  # Streamlit UI
├── scorer.py               # Composite scoring engine
├── skill_extractor.py      # Skill detection with 80+ taxonomy
├── parser.py               # PDF, DOCX, TXT parsing
├── cleaner.py              # Text normalisation
├── requirements.txt
├── tests/
│   └── test_scorer.py      # 11 unit tests
└── README.md
```

---

## Project Motivation

This project was built to bridge the gap between what candidates think is a strong CV and what recruiters and ATS systems actually look for. It demonstrates practical NLP applied to a real-world problem, with a focus on scoring transparency and honest, actionable feedback.

---

## Versioning

| Version | Key Changes |
|---|---|
| V1 | Single file, TF-IDF only, 43 hardcoded skills, TXT files only |
| V2 | Modular architecture, composite scoring, role-level detection, 80+ skills, PDF/DOCX support, formatting feedback, CSV export |
| V3 (planned) | Semantic similarity with sentence embeddings, batch CV upload and ranking |

---

## Future Improvements (V3)

- **Semantic similarity** — replace TF-IDF with sentence embeddings (`all-MiniLM-L6-v2`) so that "built RESTful APIs" matches "designed backend systems" conceptually
- **Batch upload and ranking** — upload multiple CVs against one JD and get a ranked candidate table
- **Keyword density view** — show which JD terms are most frequent but absent from the CV

---

## Author

**Oludayo Agunbiade** — Computer Science Student | Aspiring Software Engineer

- GitHub: [github.com/opki45](https://github.com/opki45)
- LinkedIn: *(add your link)*

If you found this useful, give the repo a star ⭐ — it helps a lot!
