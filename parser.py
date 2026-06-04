"""
Document parser supporting PDF, DOCX, and TXT.

Improvement over original:
- Original only accepted .txt files — this supports all real-world resume formats
- Graceful encoding fallbacks for Windows-1252 and Latin-1
- File size validation before processing
- Structured error handling with user-friendly messages
"""
import io
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def parse_uploaded_file(uploaded_file) -> str:
    """
    Extract plain text from a Streamlit UploadedFile object.
    Supports PDF, DOCX, and TXT. Raises ValueError with a human-readable
    message on failure so the UI can display it cleanly.
    """
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"'{uploaded_file.name}' is {uploaded_file.size // (1024*1024):.1f} MB. "
            "Maximum allowed size is 5 MB."
        )

    filename = uploaded_file.name.lower()
    raw_bytes = uploaded_file.read()

    if filename.endswith(".pdf"):
        return _parse_pdf(raw_bytes, filename)
    elif filename.endswith(".docx"):
        return _parse_docx(raw_bytes, filename)
    elif filename.endswith(".txt"):
        return _parse_txt(raw_bytes, filename)
    else:
        raise ValueError(f"Unsupported file type: '{uploaded_file.name}'. Please upload PDF, DOCX, or TXT.")


def _parse_pdf(raw_bytes: bytes, filename: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF support. Run: pip install pdfplumber")

    text_parts = []
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n".join(text_parts).strip()
    if not text:
        raise ValueError(
            f"No extractable text found in '{filename}'. "
            "The PDF may be scanned or image-based. Please use a text-based PDF."
        )
    logger.info("Parsed PDF '%s': %d characters extracted.", filename, len(text))
    return text


def _parse_docx(raw_bytes: bytes, filename: str) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX support. Run: pip install python-docx")

    doc = Document(io.BytesIO(raw_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ValueError(f"No text content found in '{filename}'.")
    logger.info("Parsed DOCX '%s': %d characters extracted.", filename, len(text))
    return text


def _parse_txt(raw_bytes: bytes, filename: str) -> str:
    # Try common encodings; don't assume UTF-8
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text = raw_bytes.decode(encoding).strip()
            logger.info("Decoded '%s' as %s.", filename, encoding)
            return text
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Could not decode '{filename}'. Please save it as UTF-8 and try again."
    )
