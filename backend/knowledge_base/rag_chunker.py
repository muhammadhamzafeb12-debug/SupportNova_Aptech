"""
Document Structure-Based Chunker + RAG Context Builder
Splits documents by real structure: titles → sections → paragraphs → sentences
"""
import re
from typing import List, Dict, Any, Tuple


# ------------------------------------------------------------------
# Regexes for common document structural markers
# ------------------------------------------------------------------
SECTION_PATTERNS = [
    re.compile(r'^(SECTION\s*\d+[\.:]*)', re.IGNORECASE),
    re.compile(r'^(\d+\.\s)', re.IGNORECASE),
    re.compile(r'^(ARTICLE\s*\d+)', re.IGNORECASE),
    re.compile(r'^(CHAPTER\s*\d+)', re.IGNORECASE),
    re.compile(r'^(POLICY\s*\d+)', re.IGNORECASE),
    re.compile(r'^([A-Z][A-Z\s]{4,40}:)\s'),   # ALL CAPS line → heading
]

BULLET_PATTERNS = re.compile(r'^[\-\*\•\–]\s+')


def _is_section_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pat in SECTION_PATTERNS:
        if pat.match(stripped):
            return True
    # Short ALL-CAPS line = heading
    if stripped.isupper() and 3 < len(stripped) < 80:
        return True
    return False


def _split_into_sentences(text: str) -> List[str]:
    """Basic sentence splitter (no NLTK needed)."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def structure_based_chunk(
    doc_id: str,
    title: str,
    text_content: str,
    version: str = "1.0",
    max_words: int = 100,
    overlap_sentences: int = 1,
) -> List[Dict[str, Any]]:
    """
    Document-structure-aware chunker:

    1. Detect section headings → group content under each heading
    2. Split each section into paragraphs (double newline boundary)
    3. If a paragraph > max_words → split further into sentence windows
    4. Apply sentence overlap between consecutive chunks of the same section

    Returns list of chunk dicts compatible with DocumentChunk model.
    """
    if not text_content or not text_content.strip():
        return []

    lines = text_content.splitlines()

    # ── Phase 1: Group lines into (heading, paragraph_text) units ──
    sections: List[Tuple[str, str]] = []
    current_heading = title or "General"
    current_lines: List[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # Empty line → flush current paragraph
            if current_lines:
                blob = " ".join(current_lines).strip()
                if blob:
                    sections.append((current_heading, blob))
                current_lines = []
            continue

        if _is_section_heading(line):
            if current_lines:
                blob = " ".join(current_lines).strip()
                if blob:
                    sections.append((current_heading, blob))
                current_lines = []
            current_heading = line
            continue

        current_lines.append(line)

    # Flush last group
    if current_lines:
        blob = " ".join(current_lines).strip()
        if blob:
            sections.append((current_heading, blob))

    # ── Phase 2: Split long paragraphs by sentence window ──
    chunks: List[Dict[str, Any]] = []
    chunk_index = 1

    for heading, para_text in sections:
        words = para_text.split()
        if len(words) <= max_words:
            # Paragraph fits in one chunk
            chunks.append(_make_chunk(doc_id, heading, para_text, chunk_index, version))
            chunk_index += 1
        else:
            # Split into sentence windows with overlap
            sentences = _split_into_sentences(para_text)
            window: List[str] = []
            w_count = 0
            i = 0
            while i < len(sentences):
                sent = sentences[i]
                sw = len(sent.split())
                if w_count + sw > max_words and window:
                    chunk_text = " ".join(window)
                    chunks.append(_make_chunk(doc_id, heading, chunk_text, chunk_index, version))
                    chunk_index += 1
                    # Overlap: keep last N sentences
                    window = window[-overlap_sentences:] if overlap_sentences else []
                    w_count = sum(len(s.split()) for s in window)
                window.append(sent)
                w_count += sw
                i += 1
            if window:
                chunk_text = " ".join(window)
                chunks.append(_make_chunk(doc_id, heading, chunk_text, chunk_index, version))
                chunk_index += 1

    return chunks


def _make_chunk(
    doc_id: str, heading: str, content: str, index: int, version: str
) -> Dict[str, Any]:
    return {
        "doc_id": doc_id,
        "section_id": f"{doc_id}-CHK-{index:03d}",
        "heading": heading,
        "page_number": (index // 4) + 1,
        "version": version,
        "content": content,
    }


def build_rag_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Build LLM prompt with retrieved chunks as context."""
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['document_title']} | {chunk['section_id']} | Score: {chunk['relevance_score']}]\n"
            f"{chunk['content']}"
        )

    context_text = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a company policy expert. Answer the following question ONLY using the policy documents provided below.
If the answer is not found in the documents, say "No relevant policy found."

=== RETRIEVED POLICY DOCUMENTS ===
{context_text}

=== QUESTION ===
{query}

=== ANSWER (cite the source document name and section ID) ==="""

    return prompt
