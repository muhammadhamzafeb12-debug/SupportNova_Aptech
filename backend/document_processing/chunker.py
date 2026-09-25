"""
Semantic Chunker — splits parsed document sections into coherent chunks.
Target: 200–400 words per chunk. Splits on heading boundaries first,
then further splits long sections by word count with paragraph-level awareness.

Each chunk carries: chunk_id, document_id, section, heading, page_reference, version.
"""
from __future__ import annotations
import uuid
from typing import List, Dict, Any


TARGET_MIN_WORDS = 150
TARGET_MAX_WORDS = 400


def _word_count(text: str) -> int:
    return len(text.split())


def _split_into_paragraphs(text: str) -> List[str]:
    """Split text on double newlines or sentence boundaries if needed."""
    paras = [p.strip() for p in text.split('  ') if p.strip()]
    if not paras:
        paras = [text]
    return paras


def chunk_sections(
    sections: List[Dict[str, Any]],
    document_id: str,
    version: str = "1.0",
) -> List[Dict[str, Any]]:
    """
    Convert parsed sections into storage-ready chunk dicts.
    
    Each chunk dict:
        chunk_id       : str (uuid4)
        document_id    : str
        section        : str (section label e.g. "1", "2.3" or derived from heading)
        heading        : str | None
        page_reference : int
        version        : str
        text           : str (chunk body)
        word_count     : int
    """
    chunks: List[Dict[str, Any]] = []
    section_counter = 0

    for raw_section in sections:
        page = raw_section.get("page", 1)
        heading = raw_section.get("heading") or "General"
        text = raw_section.get("text", "").strip()

        if not text:
            continue

        section_counter += 1
        section_label = f"S{section_counter}"

        words = _word_count(text)

        if words <= TARGET_MAX_WORDS:
            # Fits in a single chunk
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "section": section_label,
                "heading": heading,
                "page_reference": page,
                "version": version,
                "text": text,
                "word_count": words,
            })
        else:
            # Split at paragraph / sentence boundaries respecting word limits
            sub_idx = 0
            current_words: List[str] = []
            current_word_count = 0

            all_words = text.split()
            i = 0
            while i < len(all_words):
                current_words.append(all_words[i])
                current_word_count += 1
                i += 1

                at_natural_break = (
                    current_word_count >= TARGET_MIN_WORDS
                    and current_words[-1].endswith('.')
                )
                at_max = current_word_count >= TARGET_MAX_WORDS
                at_end = i >= len(all_words)

                if at_natural_break or at_max or at_end:
                    if current_words:
                        sub_idx += 1
                        chunks.append({
                            "chunk_id": str(uuid.uuid4()),
                            "document_id": document_id,
                            "section": f"{section_label}.{sub_idx}",
                            "heading": heading,
                            "page_reference": page,
                            "version": version,
                            "text": " ".join(current_words),
                            "word_count": current_word_count,
                        })
                        current_words = []
                        current_word_count = 0

    return chunks
