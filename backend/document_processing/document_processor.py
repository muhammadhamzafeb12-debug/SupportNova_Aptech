import os
import re
import zipfile
import shutil
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document as DocxDocument

def parse_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def parse_zip(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts and parses all PDF, DOCX, and TXT files contained within a ZIP archive.
    Returns a list of dicts: [{"filename": str, "content": str}]
    """
    results = []
    tmp_extract_dir = file_path + "_extracted"
    try:
        os.makedirs(tmp_extract_dir, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(tmp_extract_dir)
            
        for root, _, files in os.walk(tmp_extract_dir):
            for filename in files:
                if filename.startswith(".") or filename.startswith("__MACOSX"):
                    continue
                full_path = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                text = ""
                if ext == ".pdf":
                    pages = parse_pdf(full_path)
                    text = "\n".join([p["text"] for p in pages if p.get("text")])
                elif ext in [".docx", ".doc"]:
                    sections = parse_docx(full_path)
                    text = "\n".join([s["text"] for s in sections if s.get("text")])
                elif ext in [".txt", ".md", ".json", ".csv"]:
                    text = parse_txt(full_path)
                
                if text and text.strip():
                    results.append({"filename": filename, "content": text.strip()})
    except Exception as e:
        print(f"Error parsing zip file {file_path}: {e}")
    finally:
        shutil.rmtree(tmp_extract_dir, ignore_errors=True)
    return results


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    try:
        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({"page_number": i + 1, "text": text})
        return pages
    except Exception:
        return []

def parse_docx(file_path: str) -> List[Dict[str, Any]]:
    try:
        doc = DocxDocument(file_path)
        sections = []
        current_heading = "General"
        current_text = []
        
        for p in doc.paragraphs:
            if p.style.name.startswith("Heading"):
                if current_text:
                    sections.append({"heading": current_heading, "text": "\n".join(current_text)})
                    current_text = []
                current_heading = p.text
            else:
                if p.text.strip():
                    current_text.append(p.text)
        if current_text:
            sections.append({"heading": current_heading, "text": "\n".join(current_text)})
            
        return sections
    except Exception:
        return []

def split_text_into_chunks(
    text: str,
    chunk_size: int = 150,
    overlap: int = 30,
    by_characters: bool = False
) -> List[str]:
    """
    Reusable text chunking utility that splits text into smaller chunks with optional overlap.
    Can split by word count (default: 150 words with 30 word overlap) or character count.
    """
    text_clean = text.strip()
    if not text_clean:
        return []

    if by_characters:
        chunks = []
        start = 0
        text_len = len(text_clean)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text_clean[start:end].strip())
            if end == text_len:
                break
            start += (chunk_size - overlap)
        return chunks
    else:
        words = text_clean.split()
        if len(words) <= chunk_size:
            return [text_clean]

        chunks = []
        start = 0
        total_words = len(words)
        step = max(1, chunk_size - overlap)

        while start < total_words:
            end = min(start + chunk_size, total_words)
            chunk_text = " ".join(words[start:end])
            chunks.append(chunk_text)
            if end == total_words:
                break
            start += step

        return chunks

def chunk_document(
    doc_id: str,
    title: str,
    text_content: str,
    version: str = "1.0",
    chunk_size: int = 80,
    overlap: int = 20
) -> List[Dict[str, Any]]:
    """
    Splits text content into traceable chunks retaining Section, Heading, Page, Version, Doc ID.
    Splits by sections/paragraphs first, then breaks down long sections into smaller chunks of ~80 words (with 20 word overlap).
    """
    if not text_content or not text_content.strip():
        return []

    # Identify sections by headings or double newlines
    lines = text_content.split("\n")
    raw_sections = []
    current_heading = "General"
    current_lines = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # Check if line looks like a section header
        if re.match(r'^(SECTION|SECTION\s+\d+|ARTICLE|POLICY\s+\d+|CHAPTER|\d+\.\d+)', line_clean, re.IGNORECASE):
            if current_lines:
                raw_sections.append((current_heading, "\n".join(current_lines)))
                current_lines = []
            current_heading = line_clean
        else:
            current_lines.append(line_clean)

    if current_lines:
        raw_sections.append((current_heading, "\n".join(current_lines)))

    chunks = []
    chunk_index = 1

    for heading, sec_text in raw_sections:
        sub_chunks = split_text_into_chunks(sec_text, chunk_size=chunk_size, overlap=overlap)
        for sub_text in sub_chunks:
            chunks.append({
                "doc_id": doc_id,
                "section_id": f"{doc_id}-SEC-{chunk_index}",
                "heading": heading,
                "page_number": (chunk_index // 2) + 1,
                "version": version,
                "content": sub_text
            })
            chunk_index += 1

    return chunks
