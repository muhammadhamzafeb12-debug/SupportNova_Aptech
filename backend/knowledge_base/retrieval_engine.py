import math
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Policy, DocumentChunk, PolicyStatus

# Policy Precedence Weights (SRS requirement #11)
PRECEDENCE_WEIGHTS = {
    PolicyStatus.ACTIVE.value: 1.0,
    "LATEST_SOP": 0.85,
    "FAQ": 0.70,
    PolicyStatus.DRAFT.value: 0.50,
    PolicyStatus.SUPERSEDED.value: 0.10,
    PolicyStatus.OUTDATED.value: 0.0
}

def compute_tf_idf_similarity(query: str, document_text: str) -> float:
    query_words = set(re.findall(r'\w+', query.lower()))
    doc_words = re.findall(r'\w+', document_text.lower())
    
    if not query_words or not doc_words:
        return 0.0
    
    doc_word_counts = {}
    for w in doc_words:
        doc_word_counts[w] = doc_word_counts.get(w, 0) + 1
        
    score = 0.0
    for qw in query_words:
        if qw in doc_word_counts:
            # Term frequency in chunk
            tf = doc_word_counts[qw] / len(doc_words)
            score += tf * (1.0 + math.log(len(qw)))
            
    return min(1.0, score * 3.0)

import re

def retrieve_relevant_policies(db: Session, complaint_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves top relevant approved policy chunks based on semantic TF-IDF relevance and policy precedence.
    Enforces active policy hierarchy over superseded/outdated policies.
    """
    # Query active or valid policy chunks
    chunks = db.query(DocumentChunk, Policy).join(Policy, DocumentChunk.policy_id == Policy.id).all()
    
    results = []
    for chunk, policy in chunks:
        # Ignore outdated policies if active version exists
        precedence = PRECEDENCE_WEIGHTS.get(policy.status, 0.5)
        if precedence <= 0:
            continue
            
        similarity = compute_tf_idf_similarity(complaint_text, chunk.content)
        final_score = similarity * precedence
        
        if final_score > 0.05:
            results.append({
                "chunk_id": chunk.id,
                "doc_id": policy.doc_id,
                "section_id": chunk.section_id or f"{policy.doc_id}-SEC",
                "document_title": policy.title,
                "category": policy.category,
                "version": policy.version,
                "status": policy.status,
                "heading": chunk.heading or "General",
                "page": chunk.page_number,
                "effective_date": policy.effective_date or "2026-01-01",
                "source_reference": policy.source_reference,
                "content": chunk.content,
                "relevance_score": round(final_score, 4)
            })
            
    # Sort by final score descending
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_k]
