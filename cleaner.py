"""
Text normalisation for resume and job description content.

Fixes over original:
- Original used str.maketrans to strip ALL punctuation, which destroyed
  skill names like "C++", "C#", "node.js", ".NET", and "R"
- Whitespace normalisation to collapse multiple spaces/newlines
- Preserves alphanumeric tokens, dots, plus, hash (relevant to tech skills)
"""
import re


def clean_text(text: str) -> str:
    """
    Lowercase and normalise text while preserving tech-relevant punctuation.
    Strips everything except letters, digits, spaces, +, #, and dot.
    """
    text = text.lower()
    # Keep: word chars, whitespace, +, #, . (for C++, C#, node.js, .NET)
    text = re.sub(r"[^\w\s\+\#\.]", " ", text)
    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences for LLM context chunking."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]
