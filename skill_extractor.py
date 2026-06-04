"""
Skill extraction with two-stage detection.

Fixes over original:
1. Original used `skill in text` which matched substrings.
   "c" would match inside "science", "r" inside "render". 
   Now uses regex word boundaries (\b).

2. Original had 43 hardcoded skills — misses Kubernetes, Terraform,
   Rust, Go, Spark, Airflow, LangChain, etc.
   
3. Original matched skills case-insensitively but didn't handle
   "C++" → regex escapes special regex characters in skill names.

4. Skill synonyms: "machine learning" and "ml" now both map to the
   same canonical skill.
"""
import re
from typing import NamedTuple


class SkillMatch(NamedTuple):
    canonical: str   # The canonical skill name to display
    matched_term: str  # The exact term matched in the text
    count: int         # How many times it appeared


# ── Comprehensive skill taxonomy ──────────────────────────────────────────────
# Each entry: (canonical_name, [aliases])
# The canonical name is what we display; aliases are all matched patterns.

SKILL_TAXONOMY: list[tuple[str, list[str]]] = [
    # Languages
    ("Python",          ["python"]),
    ("Java",            ["java"]),
    ("JavaScript",      ["javascript", "js"]),
    ("TypeScript",      ["typescript", "ts"]),
    ("C++",             ["c\\+\\+"]),
    ("C#",              ["c#", "c sharp"]),
    ("Go",              ["golang", "\\bgo\\b"]),
    ("Rust",            ["rust"]),
    ("Ruby",            ["ruby"]),
    ("PHP",             ["php"]),
    ("Swift",           ["swift"]),
    ("Kotlin",          ["kotlin"]),
    ("Scala",           ["scala"]),
    ("R",               ["\\bR\\b"]),
    ("MATLAB",          ["matlab"]),
    ("Bash",            ["bash", "shell scripting"]),

    # Web Frontend
    ("React",           ["react", "react.js", "reactjs"]),
    ("Vue.js",          ["vue", "vue.js", "vuejs"]),
    ("Angular",         ["angular", "angularjs"]),
    ("Next.js",         ["next.js", "nextjs"]),
    ("HTML",            ["html", "html5"]),
    ("CSS",             ["css", "css3", "sass", "scss"]),
    ("Tailwind CSS",    ["tailwind"]),

    # Backend / Frameworks
    ("Node.js",         ["node.js", "nodejs", "node"]),
    ("Express.js",      ["express", "express.js"]),
    ("Django",          ["django"]),
    ("Flask",           ["flask"]),
    ("FastAPI",         ["fastapi"]),
    ("Spring Boot",     ["spring boot", "spring"]),
    (".NET",            ["\\.net", "dotnet", "asp.net"]),

    # Data & ML
    ("Pandas",          ["pandas"]),
    ("NumPy",           ["numpy"]),
    ("Scikit-learn",    ["scikit-learn", "sklearn"]),
    ("TensorFlow",      ["tensorflow"]),
    ("PyTorch",         ["pytorch"]),
    ("Keras",           ["keras"]),
    ("Machine Learning",["machine learning", "\\bml\\b"]),
    ("Deep Learning",   ["deep learning", "\\bdl\\b"]),
    ("NLP",             ["natural language processing", "\\bnlp\\b"]),
    ("LLMs",            ["large language model", "\\bllm\\b", "llms"]),
    ("LangChain",       ["langchain"]),
    ("Data Analysis",   ["data analysis", "data analytics"]),
    ("Data Visualisation", ["data visuali[sz]ation", "matplotlib", "seaborn", "plotly"]),
    ("Apache Spark",    ["spark", "pyspark", "apache spark"]),
    ("Airflow",         ["airflow", "apache airflow"]),
    ("Algorithms",       ["algorithms", "algorithm"]),
    ("Data Structures",  ["data structures", "data structure"]),
    ("Unit Testing",     ["unit test", "unit testing", "pytest", "jest"]),
    ("OOP",              ["object oriented", "oop", "object-oriented"]),

    # Databases
    ("SQL",             ["\\bsql\\b"]),
    ("MySQL",           ["mysql"]),
    ("PostgreSQL",      ["postgresql", "postgres"]),
    ("MongoDB",         ["mongodb", "mongo"]),
    ("Redis",           ["redis"]),
    ("Elasticsearch",   ["elasticsearch", "elastic"]),
    ("Snowflake",       ["snowflake"]),
    ("BigQuery",        ["bigquery"]),

    # Cloud & DevOps
    ("AWS",             ["aws", "amazon web services"]),
    ("Azure",           ["azure", "microsoft azure"]),
    ("GCP",             ["gcp", "google cloud"]),
    ("Docker",          ["docker"]),
    ("Kubernetes",      ["kubernetes", "k8s"]),
    ("Terraform",       ["terraform"]),
    ("CI/CD",           ["ci/cd", "cicd", "github actions", "jenkins", "circleci"]),
    ("Linux",           ["linux", "unix"]),
    ("Git",             ["git", "github", "gitlab"]),

    # Tools & Practices
    ("REST API",        ["rest api", "restful", "rest"]),
    ("GraphQL",         ["graphql"]),
    ("Agile",           ["agile", "scrum", "kanban"]),
    ("Excel",           ["excel", "microsoft excel"]),
    ("Power BI",        ["power bi"]),
    ("Tableau",         ["tableau"]),
    ("Jira",            ["jira"]),

    # Development practices
    ("Version Control",      ["version control"]),
    ("Unit Testing",         ["unit test", "unit testing", "pytest", "jest", "test-driven"]),
    ("Debugging",            ["debugging", "debug"]),
    ("Full Stack",           ["full stack", "full-stack"]),
    ("System Design",        ["system design", "service-oriented", "microservices", "soa"]),
    ("Prompt Engineering",   ["prompt engineering"]),
    ("Speech Recognition",   ["speech recognition", "speech-to-text"]),
    ("LLMs",                 ["large language model", "\\bllm\\b", "llms", "ollama", "generative ai", "genai"]),
    ("Open Source",          ["open.source", "open source"]),
    ("Hackathon",            ["hackathon"]),

    # Soft Skills
    ("Communication",   ["communication"]),
    ("Teamwork",        ["teamwork", "collaboration"]),
    ("Problem Solving", ["problem solving", "problem-solving"]),
    ("Leadership",      ["leadership", "team lead"]),
    ("Project Management", ["project management"]),
]


def find_skills(text: str) -> list[SkillMatch]:
    """
    Detect skills in text using word-boundary regex matching.
    Returns a list of SkillMatch with canonical name, matched term, and count.
    
    NOTE: `text` should already be lowercased (from cleaner.clean_text).
    """
    results: list[SkillMatch] = []
    seen_canonical: set[str] = set()

    for canonical, aliases in SKILL_TAXONOMY:
        canonical_lower = canonical.lower()
        if canonical_lower in seen_canonical:
            continue

        for alias in aliases:
            # Build word-boundary pattern; alias may already contain regex
            if any(c in alias for c in r"\b()[]{}^$|?*+."):
                pattern = alias  # already a regex pattern
            else:
                pattern = r"\b" + re.escape(alias) + r"\b"

            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                results.append(SkillMatch(
                    canonical=canonical,
                    matched_term=matches[0],
                    count=len(matches)
                ))
                seen_canonical.add(canonical_lower)
                break  # found via one alias, don't double-count

    return sorted(results, key=lambda x: x.canonical)


def get_canonical_set(matches: list[SkillMatch]) -> set[str]:
    return {m.canonical for m in matches}
