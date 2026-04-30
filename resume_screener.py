#AI Resume Screener
#Compares a CV with a job description and scores the CV based on relevance to the job description using NLP.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load the CV and job description
with open('cv.txt', 'r', encoding='utf-8') as file:
    cv_text = file.read()

with open('job_description.txt', 'r', encoding='utf-8') as file:
    job_description_text = file.read()

print("CV and Job Description loaded successfully.")

# Combine the CV and job description into a list for vectorization
documents = [cv_text, job_description_text]

# Vectorize the documents
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(documents)

print("Text converted into numeric vectors")

# Calculate the cosine similarity between the CV and job description
similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

match_percentage = round(similarity_score * 100, 2)
print(f"CV match score: {match_percentage}%")

if match_percentage >= 75:
    print("The CV is a strong match for the job description.")
elif match_percentage >= 50:
    print("The CV is a moderate match for the job description.")
else:
    print("The CV is a weak match for the job description.")


def clean_text(text):
    # Remove punctuation and convert to lowercase
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text

cv_text = clean_text(cv_text)
job_description_text = clean_text(job_description_text)

cv_words = set(cv_text.split())
job_description_words = set(job_description_text.split())

matching_words = cv_words.intersection(job_description_words)
print("\nWords in CV that match the job description:")
print(", ".join(sorted(matching_words)))

missing_words = job_description_words.difference(cv_words)
print("\nWords in job description not found in CV:")
print(", ".join(sorted(missing_words)))

#CHART 
labels = ["Match", "Gap"]
values = [match_percentage, 100 - match_percentage]

plt.figure()
plt.bar(labels, values)

plt.title("CV Fit Analysis")
plt.ylabel("Percentage")

plt.show()