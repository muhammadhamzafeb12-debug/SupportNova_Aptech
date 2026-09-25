"""
Document Processing Pipeline — orchestrates parse → chunk → embed → persist.
Designed to run as a FastAPI BackgroundTask (non-blocking).
Updates parsing_status on the document record throughout the pipeline.
"""
from __future__ import annotations
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any

from backend.document_processing.parser import parse_document
from backend.document_processing.chunker import chunk_sections
from backend.document_processing.retriever import add_chunks_to_index

logger = logging.getLogger(__name__)


def process_document_pipeline(
    document_id: str,
    file_path: str,
    version: str,
    kb_store: List[Dict[str, Any]],
    chunks_store: List[Dict[str, Any]],
) -> None:
    """
    Full pipeline: parse → chunk → embed → persist.
    Runs synchronously in a background thread (FastAPI BackgroundTask).
    
    Args:
        document_id  : KB-DOC-XXXX identifier for this document.
        file_path    : Absolute path to the uploaded file.
        version      : Document version string.
        kb_store     : Reference to the in-memory KNOWLEDGE_BASE_STORE list.
        chunks_store : Reference to the in-memory KB_CHUNKS_STORE list.
    """
    _set_parsing_status(kb_store, document_id, "processing", parsing_error=None)
    logger.info(f"[Pipeline] Starting document processing for {document_id} — {file_path}")

    try:
        # ── STEP 1: Parse ──────────────────────────────────────────
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        raw_sections = parse_document(file_path)
        logger.info(f"[Pipeline] Parsed {len(raw_sections)} sections from {file_path}")

        if not raw_sections:
            raise ValueError("Document produced no parseable content.")

        # ── STEP 2: Chunk ──────────────────────────────────────────
        chunks = chunk_sections(raw_sections, document_id=document_id, version=version)
        logger.info(f"[Pipeline] Created {len(chunks)} chunks for {document_id}")

        # ── STEP 3: Persist chunks to in-memory store ──────────────
        # Remove existing chunks for this document (in case of re-process)
        old_count = len(chunks_store)
        chunks_store[:] = [c for c in chunks_store if c.get("document_id") != document_id]
        if len(chunks_store) < old_count:
            logger.info(f"[Pipeline] Removed old chunks for {document_id}")
        chunks_store.extend(chunks)

        # ── STEP 4: Build FAISS embeddings ─────────────────────────
        add_chunks_to_index(chunks)
        logger.info(f"[Pipeline] Indexed {len(chunks)} chunks into FAISS for {document_id}")

        # ── STEP 5: Mark completed ─────────────────────────────────
        _set_parsing_status(kb_store, document_id, "completed", chunk_count=len(chunks))
        logger.info(f"[Pipeline] COMPLETED processing for {document_id}")

    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"[Pipeline] FAILED for {document_id}: {error_msg}\n{traceback.format_exc()}")
        _set_parsing_status(kb_store, document_id, "failed", parsing_error=error_msg)


def _set_parsing_status(
    kb_store: List[Dict[str, Any]],
    document_id: str,
    status: str,
    parsing_error: str | None = None,
    chunk_count: int | None = None,
) -> None:
    """Update the parsing_status (and optionally error/count) on the document record."""
    for doc in kb_store:
        if doc.get("document_id") == document_id:
            doc["parsing_status"] = status
            if parsing_error is not None:
                doc["parsing_error"] = parsing_error
            if chunk_count is not None:
                doc["chunk_count"] = chunk_count
            break
