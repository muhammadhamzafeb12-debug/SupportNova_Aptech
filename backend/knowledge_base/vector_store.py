"""
RAG Vector Store - TF-IDF based Embeddings & Cosine Similarity Search
Uses scikit-learn (already installed) — no extra dependencies needed.
"""
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

# below is backned line 32


# ------------------------------------------------------------------
# Global in-memory vectorizer (rebuilt on each server start / when
# build_vector_index() is called explicitly after a new upload)
# ------------------------------------------------------------------
_vectorizer: Optional[TfidfVectorizer] = None
_chunk_matrix = None        # shape (n_chunks, n_features)
_chunk_metadata: List[Dict] = []   # parallel list of chunk dicts


def build_vector_index(db: Session) -> int:
    """
    Build TF-IDF index from all chunks currently stored in DB.
    Call this once at startup and after every new document upload.
    Returns number of chunks indexed.
    """
    global _vectorizer, _chunk_matrix, _chunk_metadata

    from models import DocumentChunk, Policy

    rows = (
        db.query(DocumentChunk, Policy)
        .join(Policy, DocumentChunk.policy_id == Policy.id)
        .filter(Policy.status == "ACTIVE")
        .all()
    )

    if not rows:
        _vectorizer = None
        _chunk_matrix = None
        _chunk_metadata = []
        return 0

    texts = [chunk.content for chunk, _ in rows]
    _chunk_metadata = [
        {
            "chunk_id": chunk.id,
            "doc_id": policy.doc_id,
            "section_id": chunk.section_id,
            "heading": chunk.heading or "General",
            "page_number": chunk.page_number,
            "version": chunk.version,
            "document_title": policy.title,
            "category": policy.category,
            "status": policy.status,
            "source_reference": policy.source_reference or "",
            "content": chunk.content,
        }
        for chunk, policy in rows
    ]

    _vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )
    _chunk_matrix = _vectorizer.fit_transform(texts)
    return len(texts)


def similarity_search(
    query: str,
    top_k: int = 5,
    min_score: float = 0.01,
) -> List[Dict[str, Any]]:
    """
    Find top-k most similar chunks for a query using cosine similarity.
    Returns list of chunk dicts with relevance_score field.
    """
    global _vectorizer, _chunk_matrix, _chunk_metadata

    if _vectorizer is None or _chunk_matrix is None or not _chunk_metadata:
        return []

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _chunk_matrix).flatten()

    # Get top-k indices
    top_indices = np.argsort(scores)[::-1][:top_k * 2]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score < min_score:
            continue
        item = dict(_chunk_metadata[idx])
        item["relevance_score"] = round(score, 4)
        results.append(item)
        if len(results) >= top_k:
            break

    return results
