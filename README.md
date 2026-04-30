# AI Resume Screener

An AI-powered resume screening tool that analyses how well a CV matches a job description using Natural Language Processing (NLP).
Built to help users **optimise their CVs with data-driven insights** and improve their chances of landing interviews.


## Overview

Recruiters often scan CVs in seconds, looking for specific skills and keywords.
This project simulates that process by:

* Comparing a CV with a job description
* Calculating a similarity score using NLP
* Identifying matched and missing skills
* Providing actionable feedback for improvement

## Features

* **CV Match Score** using TF-IDF + cosine similarity
* **Skills Gap Analysis** (matched vs missing skills)
* **Visualisation** of CV fit using matplotlib
* **Improvement Suggestions** based on missing skills
* **Interactive Web App** built with Streamlit


## Tech Stack

* **Python**
* **pandas, NumPy**
* **scikit-learn** (TF-IDF, cosine similarity)
* **matplotlib**
* **Streamlit**

## How It Works

1. Upload a CV and job description
2. Text is cleaned and processed
3. TF-IDF converts text into numerical vectors
4. Cosine similarity calculates how closely they match
5. Skills are extracted and compared
6. Results are displayed with insights and visualisations

## Demo

<img width="980" height="811" alt="image" src="https://github.com/user-attachments/assets/9fa161b7-2306-4d6a-91bb-8c41bfd108cc" />
<img width="1005" height="568" alt="image" src="https://github.com/user-attachments/assets/415f6151-8d0d-435e-ac03-dd5016c3e17e" />
<img width="1138" height="538" alt="image" src="https://github.com/user-attachments/assets/993ea3e9-923c-49f3-a80c-76252b5b365b" />



Example output:

* Match Score: 68%
* Rating: Moderate Match
* Missing Skills: pandas, machine learning


## Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-resume-screener.git
cd ai-resume-screener
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python -m streamlit run app.py
```

---

## Project Structure

```text
ai-resume-screener/
│
├── app.py                # Streamlit app
├── resume_screener.py   # Core NLP logic (optional)
├── requirements.txt
└── README.md
```

## Project Motivation

This project was built to bridge the gap between:
* **what candidates think is a strong CV**
* and **what recruiters actually look for**

It demonstrates practical use of NLP for real-world problem solving in recruitment and career optimisation.

## Future Improvements

* PDF/DOCX CV parsing
* Advanced NLP using transformer models
* Job-specific skill weighting
* Deploy as a live web application
* User authentication & saved reports

## Author

**Oludayo Agunbiade**
Computer Science Student | Aspiring Software Engineer

* GitHub: https://github.com/opki45
* LinkedIn: *(add your link)*

## If you found this useful

Give the repo a star 🌟 — it helps a lot!
