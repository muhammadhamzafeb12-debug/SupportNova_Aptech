"""
Semantic Embedding & FAISS Retrieval Index for SupportNova Knowledge Base.

Primary: sentence-transformers (all-MiniLM-L6-v2) + FAISS Flat-IP.
Fallback: Lightweight TF-IDF + Cosine Similarity vector search.
Provides: retrieve_relevant_chunks(query, top_k, include_statuses) -> list of chunk dicts.

CRITICAL BUSINESS RULE:
- Default retrieval ONLY returns chunks from documents with status="Active".
- Draft and Superseded document chunks are excluded by default.
- Expired documents (where current_date > expiry_date) are EXCLUDED from Active retrieval,
  and a warning is logged.
"""
from __future__ import annotations
import math
import logging
import threading
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global state
_index = None
_chunk_metadata: List[Dict[str, Any]] = []
_model = None
_use_fallback = False
_lock = threading.Lock()

MODEL_NAME = "all-MiniLM-L6-v2"


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]+\b', text)]


def _compute_tfidf_vector(text: str, vocab: Dict[str, int], idf: Dict[str, float]) -> List[float]:
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * len(vocab)

    tf: Dict[str, int] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1

    vec = [0.0] * len(vocab)
    norm_sq = 0.0
    for term, count in tf.items():
        if term in vocab:
            idx = vocab[term]
            val = (count / len(tokens)) * idf.get(term, 1.0)
            vec[idx] = val
            norm_sq += val * val

    norm = math.sqrt(norm_sq)
    if norm > 0:
        vec = [v / norm for v in vec]

    return vec


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    return sum(a * b for a, b in zip(vec1, vec2))


def _get_model():
    global _model, _use_fallback
    if _use_fallback:
        return None

    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
            _model = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            logger.warning(f"Could not load sentence_transformers ({e}). Switching to TF-IDF retriever fallback.")
            _use_fallback = True
            return None
    return _model


def _is_doc_eligible(
    document_id: str,
    include_statuses: List[str],
    kb_store: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Check if a document is eligible for retrieval based on status and expiry date.
    Returns False if doc is not in allowed statuses or is past its expiry date.
    """
    from backend.src.store import KNOWLEDGE_BASE_STORE
    store_to_check = kb_store if kb_store is not None else KNOWLEDGE_BASE_STORE

    for doc in store_to_check:
        if doc.get("document_id") == document_id:
            status = doc.get("status", "Active")
            # 1. Check status filter
            if status not in include_statuses:
                return False

            # 2. Check expiry date rule
            expiry_str = doc.get("expiry_date")
            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    current_date = datetime.utcnow().date()
                    if current_date > expiry_date:
                        logger.warning(
                            f"EXCLUDING EXPIRED DOCUMENT '{document_id}' ('{doc.get('title')}') "
                            f"from retrieval despite status='{status}' (expired on {expiry_str})."
                        )
                        return False
                except ValueError:
                    pass  # If expiry date format fails to parse, fall back to status check
            return True

    # If document metadata not found in store, default to allowing
    return True


def add_chunks_to_index(chunks: List[Dict[str, Any]]) -> None:
    global _index, _chunk_metadata, _use_fallback

    if not chunks:
        return

    model = _get_model()

    if model is not None and not _use_fallback:
        try:
            import numpy as np
            import faiss

            texts = [c["text"] for c in chunks]
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
            dim = embeddings.shape[1]

            with _lock:
                if _index is None:
                    _index = faiss.IndexFlatIP(dim)
                _index.add(embeddings)
                _chunk_metadata.extend(chunks)
                logger.info(f"Added {len(chunks)} chunks to FAISS index (total: {_index.ntotal})")
            return
        except Exception as e:
            logger.warning(f"FAISS indexing failed: {e}. Falling back to TF-IDF search.")
            _use_fallback = True

    with _lock:
        _chunk_metadata.extend(chunks)
        logger.info(f"Added {len(chunks)} chunks to TF-IDF fallback index (total: {len(_chunk_metadata)})")


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    include_statuses: Optional[List[str]] = None,
    kb_store: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve the top_k most semantically relevant chunks for a query.
    
    CRITICAL BUSINESS RULE:
    - Default include_statuses is ["Active"]. Draft and Superseded chunks are excluded by default.
    - Documents past expiry_date are excluded from Active retrieval, and a warning is logged.
    """
    global _index, _chunk_metadata, _use_fallback

    if include_statuses is None:
        include_statuses = ["Active"]

    if not _chunk_metadata:
        logger.warning("Search index is empty — returning empty results.")
        return []

    # Filter eligible chunks first by document status and expiry
    eligible_chunks = [
        c for c in _chunk_metadata
        if _is_doc_eligible(c.get("document_id", ""), include_statuses, kb_store)
    ]

    if not eligible_chunks:
        logger.info("No chunks passed status/expiry eligibility filter.")
        return []

    model = _get_model()

    if model is not None and not _use_fallback and _index is not None and _index.ntotal > 0:
        try:
            import numpy as np
            query_vec = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
            with _lock:
                k = min(top_k * 3, _index.ntotal)
                scores, indices = _index.search(query_vec, k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or idx >= len(_chunk_metadata):
                    continue
                chunk = _chunk_metadata[idx]
                if _is_doc_eligible(chunk.get("document_id", ""), include_statuses, kb_store):
                    c_dict = dict(chunk)
                    c_dict["relevance_score"] = float(score)
                    results.append(c_dict)

            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.warning(f"FAISS search failed: {e}. Using TF-IDF fallback.")

    # ── TF-IDF Fallback search on eligible_chunks ─────────────────────────────
    query_tokens = _tokenize(query)
    if not query_tokens:
        return [dict(c, relevance_score=0.0) for c in eligible_chunks[:top_k]]

    all_tokens_set = set(query_tokens)
    doc_freq: Dict[str, int] = {}

    for chunk in eligible_chunks:
        tokens = set(_tokenize(chunk["text"]))
        all_tokens_set.update(tokens)
        for t in tokens:
            doc_freq[t] = doc_freq.get(t, 0) + 1

    vocab = {t: i for i, t in enumerate(all_tokens_set)}
    N = max(1, len(eligible_chunks))
    idf = {t: math.log((N + 1) / (df + 1)) + 1 for t, df in doc_freq.items()}

    query_vec = _compute_tfidf_vector(query, vocab, idf)

    scored_chunks = []
    for chunk in eligible_chunks:
        c_vec = _compute_tfidf_vector(chunk["text"], vocab, idf)
        score = _cosine_similarity(query_vec, c_vec)
        heading = (chunk.get("heading") or "").lower()
        if any(qt in heading for qt in query_tokens):
            score += 0.2
        scored_chunks.append(dict(chunk, relevance_score=round(score, 4)))

    scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_chunks[:top_k]


def remove_document_chunks(document_id: str) -> None:
    """Remove all chunks of a document from the index."""
    global _index, _chunk_metadata
    with _lock:
        _chunk_metadata = [c for c in _chunk_metadata if c.get("document_id") != document_id]
        _index = None


def index_size() -> int:
    return len(_chunk_metadata)
