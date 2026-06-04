"""
Composite CV scoring engine.

Improvements over original:
- Original had a single 'keyword similarity' score from TF-IDF and a 'skills match'
  percentage — two unrelated numbers shown side by side with no explanation.
  
- New: weighted composite score with four named components:
    1. Skills match (40%)  — what can you actually do?
    2. Keyword similarity (30%) — language alignment
    3. Experience match (15%) — years of experience vs requirement
    4. Education match (15%) — degree level vs requirement
    
- Each component explains its own contribution.
- Final score is 0–100 with a calibrated label.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skill_extractor import find_skills, get_canonical_set, SkillMatch


# ── Weights ───────────────────────────────────────────────────────────────────
WEIGHTS = {
    "intern": {"skills": 0.75, "keyword": 0.00, "experience": 0.10, "education": 0.15},
    "mid":    {"skills": 0.40, "keyword": 0.30, "experience": 0.15, "education": 0.15},
    "senior": {"skills": 0.35, "keyword": 0.25, "experience": 0.30, "education": 0.10},
}

def _detect_role_level(job_text: str) -> str:
    """Returns 'intern', 'senior', or 'mid' based on JD language."""
    text_lower = job_text.lower()
    
    intern_signals = ["intern", "internship", "placement", "penultimate year", 
                      "entry level", "entry-level", "graduate scheme", "grad scheme",
                      "new graduate", "recent graduate", "junior", "apprentice"]
    
    senior_signals = ["senior", "lead engineer", "principal", "staff engineer",
                      "7+ years", "8+ years", "10+ years", "head of engineering",
                      "engineering manager", "tech lead"]
    
    intern_hits  = sum(1 for s in intern_signals if s in text_lower)
    senior_hits  = sum(1 for s in senior_signals if s in text_lower)
    
    if intern_hits >= 1:
        return "intern"
    elif senior_hits >= 1:
        return "senior"
    return "mid"


# ── Thresholds ────────────────────────────────────────────────────────────────
STRONG_THRESHOLD   = 70
MODERATE_THRESHOLD = 45


@dataclass
class ScoreComponent:
    name: str
    score: float          # 0–100
    weight: float
    explanation: str


@dataclass
class ScreeningResult:
    composite_score: float
    rating: str
    summary: str
    composite_summary: str 
    role_level: str
    components: list[ScoreComponent]
    cv_skills: list[SkillMatch]
    job_skills: list[SkillMatch]
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]    # CV skills not in JD (bonus context for recruiter)
    cv_yoe: Optional[int]
    job_yoe_required: Optional[int]
    interview_questions: list[str] = field(default_factory=list)
    formatting_notes: list[dict] = field(default_factory=list) 


def screen_cv(cv_text: str, job_text: str) -> ScreeningResult:
    """Full screening pipeline. Returns a ScreeningResult."""
    from cleaner import clean_text

    clean_cv  = clean_text(cv_text)
    clean_job = clean_text(job_text)

    # ── Skills ────────────────────────────────────────────────────────────────
    cv_skills  = find_skills(clean_cv)
    job_skills = find_skills(clean_job)
    cv_set     = get_canonical_set(cv_skills)
    job_set    = get_canonical_set(job_skills)

    matched = sorted(cv_set & job_set)
    missing = sorted(job_set - cv_set)
    extra   = sorted(cv_set - job_set)

    
    if job_set:
        base_pct = 100 * len(matched) / len(job_set)
        job_skill_counts = {m.canonical: m.count for m in job_skills}
        # Skills mentioned more than once get a small bonus, max 10 points
        frequency_bonus = sum(
            min(job_skill_counts.get(s, 1) - 1, 2) * 2
            for s in matched
        )
        skills_pct = min(100.0, base_pct + frequency_bonus)
    else:
        skills_pct = 0.0

    skills_explanation = (
        f"Matched {len(matched)} of {len(job_set)} required skills. "
        + (f"Missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}." if missing else "All detected skills present.")
    )

    # ── Keyword similarity (TF-IDF cosine) ────────────────────────────────────
    vectorizer  = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf       = vectorizer.fit_transform([cv_text, job_text])
    keyword_pct = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]) * 100

    keyword_explanation = (
        f"Vocabulary and phrasing overlap score: {keyword_pct:.0f}%. "
        "This measures how similar the language of your CV is to the job description."
    )

    # ── Experience ────────────────────────────────────────────────────────────
    cv_yoe  = _extract_max_yoe(cv_text)
    req_yoe = _extract_required_yoe(job_text)

    if req_yoe and cv_yoe is not None:
        if cv_yoe >= req_yoe:
            exp_pct = 100.0
            exp_explanation = f"You have ~{cv_yoe} years of experience; the role requires {req_yoe}+."
        else:
            exp_pct = max(0, 100 * cv_yoe / req_yoe)
            exp_explanation = (
                f"You have ~{cv_yoe} years of experience but {req_yoe}+ are required. "
                "Consider highlighting relevant project experience."
            )
    elif req_yoe and cv_yoe is None:
        exp_pct = 50.0  # can't tell; neutral
        exp_explanation = f"The role requires {req_yoe}+ years but your CV doesn't clearly state your total experience."
    else:
        exp_pct = 70.0  # no explicit requirement detected
        exp_explanation = "No specific experience requirement detected in the job description."

    # ── Education ─────────────────────────────────────────────────────────────
    cv_edu   = _detect_education_level(cv_text)
    req_edu  = _detect_required_education(job_text)
    edu_pct, edu_explanation = _score_education(cv_edu, req_edu)

    # ── Composite ─────────────────────────────────────────────────────────────
    role_level = _detect_role_level(job_text)
    w = WEIGHTS[role_level]

    composite = sum(
    getattr_score * weight
    for getattr_score, weight in [
        (skills_pct,  w["skills"]),
        (keyword_pct, w["keyword"]),
        (exp_pct,     w["experience"]),
        (edu_pct,     w["education"]),
    ]
    if weight > 0
    )

    if composite >= STRONG_THRESHOLD:
        rating  = "Strong Match"
        summary = "Your CV aligns well with this role. Tailor your opening summary to mirror the job's key priorities."
    elif composite >= MODERATE_THRESHOLD:
        rating  = "Moderate Match"
        summary = "There's meaningful overlap, but several key skills or experiences are absent. Strengthen the relevant sections."
    else:
        rating  = "Weak Match"
        summary = "Your CV is missing several key requirements. Consider upskilling or applying to roles that better match your current profile."

    components = [
        ScoreComponent("Skills match",       skills_pct,  w["skills"],     skills_explanation),
        ScoreComponent("Keyword similarity", keyword_pct, w["keyword"],    keyword_explanation),
        ScoreComponent("Experience",         exp_pct,     w["experience"], exp_explanation),
        ScoreComponent("Education",          edu_pct,     w["education"],  edu_explanation),
    ]

    questions = _generate_interview_questions(missing, cv_yoe, req_yoe)

    summary_paragraph = _generate_candidate_summary(
        composite, rating, matched, missing, cv_yoe, req_yoe, cv_edu
    )

    formatting_notes = analyse_cv_formatting(cv_text)

    return ScreeningResult(
        composite_score    = round(composite, 1),
        rating             = rating,
        summary            = summary,
        composite_summary  = summary_paragraph,
        role_level         = role_level,
        components         = components,
        cv_skills          = cv_skills,
        job_skills         = job_skills,
        matched_skills     = matched,
        missing_skills     = missing,
        extra_skills       = extra,
        cv_yoe             = cv_yoe,
        job_yoe_required   = req_yoe,
        interview_questions= questions,
        formatting_notes   = formatting_notes,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

_YOE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
    re.IGNORECASE
)

def _extract_max_yoe(text: str) -> Optional[int]:
    matches = _YOE_PATTERN.findall(text)
    if matches:
        return max(int(m) for m in matches)
    return None

def _extract_required_yoe(job_text: str) -> Optional[int]:
    # Look for patterns like "3+ years", "minimum 2 years", "at least 5 years"
    patterns = [
        r"(?:minimum|at least|requires?)\s+(\d+)\+?\s*years?",
        r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)",
    ]
    for p in patterns:
        m = re.search(p, job_text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


_EDU_LEVELS = {
    "phd":     5, "doctorate": 5, "ph.d": 5,
    "master":  4, "msc":       4, "mba": 4, "m.sc": 4,
    "bachelor":3, "bsc":       3, "b.sc": 3, "undergraduate": 3,
    "diploma": 2, "hnd":       2,
    "a-level": 1, "high school": 1,
}

def _detect_education_level(text: str) -> Optional[int]:
    text_lower = text.lower()
    for keyword, level in sorted(_EDU_LEVELS.items(), key=lambda x: -x[1]):
        if keyword in text_lower:
            return level
    return None

def _detect_required_education(text: str) -> Optional[int]:
    text_lower = text.lower()
    for keyword, level in sorted(_EDU_LEVELS.items(), key=lambda x: -x[1]):
        if keyword in text_lower:
            return level
    return None

_EDU_LABELS = {5: "PhD", 4: "Master's", 3: "Bachelor's", 2: "Diploma", 1: "A-Level/HS", None: "unspecified"}

def _score_education(cv_level: Optional[int], req_level: Optional[int]) -> tuple[float, str]:
    if req_level is None:
        return 70.0, "No specific education requirement detected."
    if cv_level is None:
        return 50.0, f"The role prefers {_EDU_LABELS[req_level]}, but your CV doesn't clearly state your education level."
    if cv_level >= req_level:
        return 100.0, f"Your {_EDU_LABELS[cv_level]} meets the {_EDU_LABELS[req_level]} requirement."
    gap = req_level - cv_level
    score = max(0, 100 - gap * 25)
    return float(score), f"The role requires {_EDU_LABELS[req_level]}; your highest detected qualification is {_EDU_LABELS[cv_level]}."

_INTERVIEW_TEMPLATES = [
    "Can you describe any exposure you've had to {skill}, even in a self-directed or personal project context?",
    "Have you worked alongside colleagues who used {skill}? What did you observe or pick up?",
    "If you had two weeks to get up to speed on {skill}, what would your learning plan look like?",
    "How would you approach a task that required {skill} given your current experience?",
    ]

def _generate_interview_questions(missing_skills: list[str], cv_yoe, req_yoe) -> list[str]:
    import random
    questions = []
    templates = _INTERVIEW_TEMPLATES.copy()
    random.shuffle(templates)
    for i, skill in enumerate(missing_skills[:4]):
        template = templates[i % len(templates)]
        questions.append(template.format(skill=skill))
    if req_yoe and cv_yoe and cv_yoe < req_yoe:
        questions.append(
            f"This role requires {req_yoe}+ years of experience. What projects best demonstrate your depth despite having {cv_yoe} years?"
        )
    return questions

def _generate_candidate_summary(score, rating, matched, missing, cv_yoe, req_yoe, cv_edu) -> str:
    parts = []

    if cv_yoe:
        parts.append(f"This candidate has approximately {cv_yoe} years of experience")
        if req_yoe and cv_yoe >= req_yoe:
            parts[-1] += f", meeting the {req_yoe}+ year requirement."
        elif req_yoe:
            parts[-1] += f", falling short of the {req_yoe}+ year requirement."
        else:
            parts[-1] += "."
    else:
        parts.append("Experience level could not be determined from the CV.")

    if matched:
        top = ", ".join(matched[:5])
        parts.append(f"Key matching skills include {top}{'and others' if len(matched) > 5 else ''}.")

    if missing:
        top_missing = ", ".join(missing[:4])
        parts.append(f"Notable gaps against the job description are {top_missing}.")
    else:
        parts.append("No significant skill gaps were detected.")

    if score >= 75:
        parts.append("Overall this is a strong application that warrants a closer look.")
    elif score >= 45:
        parts.append("This application shows potential but would benefit from a tailored cover letter addressing the gaps.")
    else:
        parts.append("This application may not be a strong fit for this specific role as written.")

    return " ".join(parts)

def analyse_cv_formatting(cv_text: str) -> list[dict]:
    """
    Returns a list of formatting observations.
    Each item has 'level' (good/warning/error) and 'message'.
    """
    observations = []
    word_count = len(cv_text.split())
    line_count = len([l for l in cv_text.splitlines() if l.strip()])

    # Length check (~400 words per page)
    if word_count < 200:
        observations.append({"level": "error", "message": f"Your CV is very short ({word_count} words). A strong CV is typically 400–800 words."})
    elif word_count > 1200:
        observations.append({"level": "warning", "message": f"Your CV is quite long ({word_count} words). Most recruiters prefer a maximum of two pages (~800 words)."})
    else:
        observations.append({"level": "good", "message": f"CV length looks good ({word_count} words)."})

    # Bullet points
    bullet_lines = len([l for l in cv_text.splitlines() if l.strip().startswith(("-", "•", "*", "·"))])
    if bullet_lines < 3:
        observations.append({"level": "warning", "message": "Few or no bullet points detected. Bullet points make CVs easier to scan and are strongly preferred by recruiters."})
    else:
        observations.append({"level": "good", "message": f"Good use of bullet points ({bullet_lines} detected)."})

    # Key sections
    text_lower = cv_text.lower()
    for section in ["experience", "education", "skills"]:
        if section not in text_lower:
            observations.append({"level": "warning", "message": f"No '{section}' section detected. Make sure this heading is clearly present."})

    # Contact info signals
    has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cv_text))
    if not has_email:
        observations.append({"level": "error", "message": "No email address detected. Make sure your contact details are included."})
    else:
        observations.append({"level": "good", "message": "Email address detected."})

    return observations