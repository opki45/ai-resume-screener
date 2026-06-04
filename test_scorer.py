"""
Tests for the skill extractor and scorer.

Run: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.cleaner import clean_text
from core.skill_extractor import find_skills, get_canonical_set


class TestCleaner:
    def test_preserves_cpp(self):
        result = clean_text("Experience with C++ and Python.")
        assert "c++" in result

    def test_preserves_csharp(self):
        result = clean_text("Proficient in C# and .NET.")
        assert "c#" in result

    def test_preserves_nodejs(self):
        result = clean_text("Built APIs in Node.js")
        assert "node.js" in result

    def test_lowercases(self):
        assert clean_text("Python") == "python"

    def test_collapses_whitespace(self):
        assert "  " not in clean_text("hello   world")


class TestSkillExtractor:
    def test_no_false_positive_c_in_science(self):
        """'C' should not match inside 'science'."""
        # 'R' and 'C' are tricky — they must only match standalone
        text = clean_text("I studied data science and economics.")
        skills = get_canonical_set(find_skills(text))
        assert "C++" not in skills

    def test_python_detected(self):
        text = clean_text("5 years of Python development")
        skills = get_canonical_set(find_skills(text))
        assert "Python" in skills

    def test_kubernetes_detected(self):
        """Kubernetes was missing from the original 43-item list."""
        text = clean_text("Deployed microservices on Kubernetes (k8s).")
        skills = get_canonical_set(find_skills(text))
        assert "Kubernetes" in skills

    def test_cpp_detected(self):
        text = clean_text("Low-level development in C++.")
        skills = get_canonical_set(find_skills(text))
        assert "C++" in skills

    def test_no_duplicate_skills(self):
        text = clean_text("Python python PYTHON")
        skills = find_skills(text)
        canonical_names = [s.canonical for s in skills]
        assert len(canonical_names) == len(set(canonical_names))

    def test_match_count(self):
        text = clean_text("Python Python Python Flask")
        skills = {s.canonical: s for s in find_skills(text)}
        assert skills["Python"].count == 3
        assert skills["Flask"].count == 1
