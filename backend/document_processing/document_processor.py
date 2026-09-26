import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from docx import Document as DocxDocument

def parse_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

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

def chunk_document(doc_id: str, title: str, text_content: str, version: str = "1.0", chunk_size: int = 400) -> List[Dict[str, Any]]:
    """
    Splits text content into traceable chunks retaining Section, Heading, Page, Version, Doc ID.
    """
    lines = text_content.split("\n")
    chunks = []
    current_chunk = []
    current_heading = "General"
    chunk_index = 1
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # Check if line looks like a section header
        if re.match(r'^(SECTION|SECTION\s+\d+|ARTICLE|POLICY\s+\d+|CHAPTER|\d+\.\d+)', line_clean, re.IGNORECASE):
            current_heading = line_clean
            
        current_chunk.append(line_clean)
        combined_text = " ".join(current_chunk)
        
        if len(combined_text.split()) >= chunk_size:
            chunks.append({
                "doc_id": doc_id,
                "section_id": f"{doc_id}-SEC-{chunk_index}",
                "heading": current_heading,
                "page_number": (chunk_index // 2) + 1,
                "version": version,
                "content": combined_text
            })
            chunk_index += 1
            current_chunk = []
            
    if current_chunk:
        chunks.append({
            "doc_id": doc_id,
            "section_id": f"{doc_id}-SEC-{chunk_index}",
            "heading": current_heading,
            "page_number": (chunk_index // 2) + 1,
            "version": version,
            "content": " ".join(current_chunk)
        })
        
    return chunks
