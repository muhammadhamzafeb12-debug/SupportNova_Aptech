"""
Document Parser — PDF (pdfplumber + PyMuPDF fallback) and DOCX
Extracts: document title, section headings, page numbers, and body text.
Returns a list of raw extracted sections with page references.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def _heading_confidence(text: str) -> bool:
    """Heuristic to detect headings: short, possibly ALL-CAPS or numbered."""
    text = text.strip()
    if not text:
        return False
    if len(text) > 120:
        return False
    # Numbered section heading: "1.", "2.1", "Section 1:"
    import re
    if re.match(r'^(\d+[\.\d]*\.?\s|section\s+\d+|chapter\s+\d+|appendix)', text, re.IGNORECASE):
        return True
    # ALL CAPS heading (at least 4 chars, no sentence structure)
    if text.isupper() and len(text) >= 4:
        return True
    # Bold-like: very short line that ends without a period
    if len(text.split()) <= 8 and not text.endswith('.') and not text.endswith(','):
        return True
    return False


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a PDF file using pdfplumber (preferred) with PyMuPDF fallback.
    Returns list of dicts: {page: int, heading: str | None, text: str}
    """
    sections: List[Dict[str, Any]] = []

    # --- pdfplumber path ---
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                raw_text = page.extract_text() or ""
                lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

                current_heading = None
                current_text_lines: List[str] = []

                for line in lines:
                    if _heading_confidence(line):
                        # Flush current section
                        if current_text_lines:
                            sections.append({
                                "page": page_num,
                                "heading": current_heading,
                                "text": " ".join(current_text_lines)
                            })
                        current_heading = line
                        current_text_lines = []
                    else:
                        current_text_lines.append(line)

                # Flush remaining text on this page
                if current_text_lines:
                    sections.append({
                        "page": page_num,
                        "heading": current_heading,
                        "text": " ".join(current_text_lines)
                    })

        if sections:
            return sections

    except Exception as e:
        logger.warning(f"pdfplumber failed for '{file_path}': {e}. Falling back to PyMuPDF.")

    # --- PyMuPDF fallback ---
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            raw_text = page.get_text("text") or ""
            lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

            current_heading = None
            current_text_lines = []

            for line in lines:
                if _heading_confidence(line):
                    if current_text_lines:
                        sections.append({
                            "page": page_num,
                            "heading": current_heading,
                            "text": " ".join(current_text_lines)
                        })
                    current_heading = line
                    current_text_lines = []
                else:
                    current_text_lines.append(line)

            if current_text_lines:
                sections.append({
                    "page": page_num,
                    "heading": current_heading,
                    "text": " ".join(current_text_lines)
                })

        doc.close()
        return sections

    except Exception as e:
        logger.error(f"PyMuPDF also failed for '{file_path}': {e}")
        raise RuntimeError(f"PDF parsing failed for {file_path}: {e}")


def parse_docx(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a DOCX file using python-docx.
    Detects headings via paragraph style names.
    Returns list of dicts: {page: int, heading: str | None, text: str}
    """
    try:
        import docx
        doc = docx.Document(file_path)
    except Exception as e:
        raise RuntimeError(f"DOCX parsing failed for {file_path}: {e}")

    sections: List[Dict[str, Any]] = []
    current_heading = None
    current_text_lines: List[str] = []
    # DOCX has no real page numbers — use paragraph count groupings
    para_counter = 0
    estimated_page = 1
    PARAS_PER_PAGE = 15  # rough estimate

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        para_counter += 1
        estimated_page = max(1, para_counter // PARAS_PER_PAGE + 1)

        # Check if paragraph is a heading by style
        style_name = para.style.name.lower() if para.style else ""
        is_heading = ("heading" in style_name) or _heading_confidence(text)

        if is_heading:
            if current_text_lines:
                sections.append({
                    "page": estimated_page,
                    "heading": current_heading,
                    "text": " ".join(current_text_lines)
                })
            current_heading = text
            current_text_lines = []
        else:
            current_text_lines.append(text)

    # Flush remaining
    if current_text_lines:
        sections.append({
            "page": estimated_page,
            "heading": current_heading,
            "text": " ".join(current_text_lines)
        })

    return sections


def parse_text(file_path: str) -> List[Dict[str, Any]]:
    """Parse plain text, Markdown, or CSV files."""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Text file parsing failed for {file_path}: {e}")

    sections: List[Dict[str, Any]] = []
    lines = content.split('\n')
    current_heading = None
    current_text_lines: List[str] = []
    page = 1

    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        # Markdown-style headings
        if text.startswith('#'):
            if current_text_lines:
                sections.append({"page": page, "heading": current_heading, "text": " ".join(current_text_lines)})
            current_heading = text.lstrip('#').strip()
            current_text_lines = []
        elif _heading_confidence(text):
            if current_text_lines:
                sections.append({"page": page, "heading": current_heading, "text": " ".join(current_text_lines)})
            current_heading = text
            current_text_lines = []
        else:
            current_text_lines.append(text)

        # Estimate page every ~40 lines
        if i > 0 and i % 40 == 0:
            page += 1

    if current_text_lines:
        sections.append({"page": page, "heading": current_heading, "text": " ".join(current_text_lines)})

    return sections


def parse_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Universal document parser. Dispatches to the right parser by extension.
    Returns structured sections list.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    elif ext in {".txt", ".md", ".csv"}:
        return parse_text(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
