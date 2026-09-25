"""
Knowledge Base API Router
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.schemas.schemas import KBDocumentCreate, KBDocumentResponse
from backend.security.jwt_auth import get_current_user, require_role
from backend.src.store import KNOWLEDGE_BASE_STORE

router = APIRouter(prefix="/knowledge_base", tags=["Knowledge Base"])

@router.get("", response_model=List[KBDocumentResponse])
def search_knowledge_base(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    results = list(KNOWLEDGE_BASE_STORE)
    if category:
        results = [d for d in results if d.get("category", "").lower() == category.lower()]
    if query:
        q = query.lower()
        results = [
            d for d in results 
            if q in d.get("title", "").lower() 
            or q in (d.get("content") or "").lower() 
            or q in (d.get("tags") or "").lower()
            or q in d.get("file_name", "").lower()
        ]
    return results

@router.post("", response_model=KBDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_document(
    payload: KBDocumentCreate,
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
):
    new_id = max([d["id"] for d in KNOWLEDGE_BASE_STORE] or [0]) + 1
    doc = {
        "id": new_id,
        "document_id": f"KB-DOC-{1000 + new_id}",
        "title": payload.title,
        "category": payload.category,
        "version": "1.0",
        "status": "Active",
        "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "content": payload.content,
        "file_name": f"doc_{new_id}.pdf",
        "tags": payload.tags or "",
        "created_at": datetime.utcnow().isoformat()
    }
    KNOWLEDGE_BASE_STORE.insert(0, doc)
    return doc

@router.get("/{doc_id}", response_model=KBDocumentResponse)
def get_knowledge_document(doc_id: int, current_user: dict = Depends(get_current_user)):
    for doc in KNOWLEDGE_BASE_STORE:
        if doc["id"] == doc_id:
            return doc
    raise HTTPException(status_code=404, detail="Knowledge Document not found")

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(
    doc_id: int,
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
):
    global KNOWLEDGE_BASE_STORE
    idx_to_remove = None
    for i, doc in enumerate(KNOWLEDGE_BASE_STORE):
        if doc["id"] == doc_id:
            idx_to_remove = i
            break
    if idx_to_remove is None:
        raise HTTPException(status_code=404, detail="Knowledge Document not found")
    
    KNOWLEDGE_BASE_STORE.pop(idx_to_remove)
    return None
