"""
Admin Knowledge Base Upload & Policy Lifecycle API Router
Handles file upload, SHA-256 deduplication, versioning (Superseded/Active/Draft),
BackgroundTask parsing pipeline, audit trail history, and draft document activation.
"""
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks, Body
from fastapi.responses import JSONResponse

from backend.schemas.schemas import KBDocumentResponse, ActivateDocumentRequest, KBVersionAuditResponse
from backend.security.jwt_auth import require_role
from backend.src.store import KNOWLEDGE_BASE_STORE, KB_CHUNKS_STORE, KB_VERSION_AUDIT_STORE
from backend.document_processing.pipeline import process_document_pipeline

router = APIRouter(prefix="/admin/knowledge-base", tags=["Admin Knowledge Base"])

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sample_documents"
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def make_error_response(error_code: str, message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": error_code,
            "error_code": error_code,
            "message": message
        }
    )


def _normalize(val: str) -> str:
    return (val or "").strip().lower()


# ── List all KB documents ──────────────────────────────────────────────────────

@router.get("", response_model=List[KBDocumentResponse])
def list_admin_kb_documents(
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    return KNOWLEDGE_BASE_STORE


# ── Upload new document with Version & Supersede Logic ─────────────────────────

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_kb_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    version: str = Form("1.0"),
    effective_date: str = Form(...),
    expiry_date: Optional[str] = Form(None),
    is_draft: Optional[bool] = Form(False),
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    filename = file.filename or "uploaded_doc"
    ext = Path(filename).suffix.lower()

    # 1. Validate file extension
    if ext not in ALLOWED_EXTENSIONS:
        return make_error_response(
            "unsupported_file_type",
            f"Unsupported file format '{ext}'. Only PDF, DOCX, TXT, MD, CSV files are allowed."
        )

    content = await file.read()
    file_size = len(content)

    # 2. Validate empty file
    if file_size == 0:
        return make_error_response("empty_file", "Uploaded file is empty (0 bytes).")

    # 3. Validate file size limit
    if file_size > MAX_FILE_SIZE:
        return make_error_response(
            "file_too_large",
            f"File size ({round(file_size / (1024*1024), 2)}MB) exceeds maximum allowed limit of 20MB."
        )

    # 4. SHA-256 deduplication
    sha256_hash = hashlib.sha256(content).hexdigest()
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("content_hash") == sha256_hash:
            return make_error_response(
                "duplicate_document",
                "Duplicate document detected. Content SHA-256 hash already exists in Knowledge Base."
            )

    # Determine status of new document
    new_doc_status = "Draft" if is_draft else "Active"
    admin_user = current_user.get("username") or current_user.get("email") or "admin@nexalink.com"

    # 5. POLICY LIFECYCLE: If new doc is Active, supersede existing Active docs with same title+category
    superseded_docs = []
    if new_doc_status == "Active":
        norm_title = _normalize(title)
        norm_category = _normalize(category)

        for doc in KNOWLEDGE_BASE_STORE:
            if (
                _normalize(doc.get("title")) == norm_title
                and _normalize(doc.get("category")) == norm_category
                and doc.get("status") == "Active"
            ):
                doc["status"] = "Superseded"
                superseded_docs.append(doc)
                # Audit log for superseded doc
                audit_id = len(KB_VERSION_AUDIT_STORE) + 1
                KB_VERSION_AUDIT_STORE.insert(0, {
                    "id": audit_id,
                    "document_id": doc.get("document_id"),
                    "title": doc.get("title"),
                    "category": doc.get("category"),
                    "previous_status": "Active",
                    "new_status": "Superseded",
                    "previous_version": doc.get("version"),
                    "new_version": version,
                    "changed_at": datetime.utcnow().isoformat(),
                    "changed_by": admin_user,
                    "reason": f"Superseded by new version {version}"
                })

    # Save file to sample_documents/
    save_path = SAMPLE_DOCS_DIR / filename
    with open(save_path, "wb") as f:
        f.write(content)

    # Auto-generate Document ID
    new_id = max([d.get("id", 0) for d in KNOWLEDGE_BASE_STORE] or [0]) + 1
    doc_id = f"KB-DOC-{1000 + new_id}"

    doc_record = {
        "id": new_id,
        "document_id": doc_id,
        "title": title,
        "category": category,
        "version": version,
        "status": new_doc_status,
        "effective_date": effective_date,
        "expiry_date": expiry_date or None,
        "file_name": filename,
        "file_path": str(save_path),
        "content_hash": sha256_hash,
        "parsing_status": "pending",
        "parsing_error": None,
        "chunk_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    KNOWLEDGE_BASE_STORE.insert(0, doc_record)

    # Audit log for new doc upload
    audit_id = len(KB_VERSION_AUDIT_STORE) + 1
    KB_VERSION_AUDIT_STORE.insert(0, {
        "id": audit_id,
        "document_id": doc_id,
        "title": title,
        "category": category,
        "previous_status": None,
        "new_status": new_doc_status,
        "previous_version": None,
        "new_version": version,
        "changed_at": datetime.utcnow().isoformat(),
        "changed_by": admin_user,
        "reason": "Initial draft upload" if is_draft else "Initial active version upload"
    })

    # Trigger processing pipeline
    background_tasks.add_task(
        process_document_pipeline,
        document_id=doc_id,
        file_path=str(save_path),
        version=version,
        kb_store=KNOWLEDGE_BASE_STORE,
        chunks_store=KB_CHUNKS_STORE,
    )

    return doc_record


# ── Get Document Parsing Status ───────────────────────────────────────────────

@router.get("/{document_id}/status")
def get_document_status(
    document_id: str,
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("document_id") == document_id:
            return {
                "document_id": document_id,
                "parsing_status": doc.get("parsing_status", "pending"),
                "chunk_count": doc.get("chunk_count", 0),
                "parsing_error": doc.get("parsing_error"),
            }
    raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")


# ── Get Document Chunks ────────────────────────────────────────────────────────

@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: str,
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    doc_found = any(d.get("document_id") == document_id for d in KNOWLEDGE_BASE_STORE)
    if not doc_found:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    chunks = [c for c in KB_CHUNKS_STORE if c.get("document_id") == document_id]
    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "chunks": chunks
    }


# ── GET Document Version History Chain ─────────────────────────────────────────

@router.get("/{document_id}/history")
def get_document_history(
    document_id: str,
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    # Find target document
    target_doc = None
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("document_id") == document_id:
            target_doc = doc
            break

    if not target_doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    norm_title = _normalize(target_doc.get("title"))
    norm_category = _normalize(target_doc.get("category"))

    # Find all documents sharing title and category
    related_docs = [
        d for d in KNOWLEDGE_BASE_STORE
        if _normalize(d.get("title")) == norm_title and _normalize(d.get("category")) == norm_category
    ]

    related_ids = {d.get("document_id") for d in related_docs}

    # Fetch audit logs for related documents
    history_audits = [
        a for a in KB_VERSION_AUDIT_STORE
        if a.get("document_id") in related_ids
    ]

    # Combine documents metadata with audit history
    history_entries = []
    for doc in related_docs:
        d_id = doc.get("document_id")
        doc_audits = [a for a in history_audits if a.get("document_id") == d_id]
        latest_audit = doc_audits[0] if doc_audits else {}

        # Compute client-side expired flag
        is_expired = False
        expiry_str = doc.get("expiry_date")
        if expiry_str:
            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if datetime.utcnow().date() > exp_date:
                    is_expired = True
            except ValueError:
                pass

        history_entries.append({
            "document_id": d_id,
            "title": doc.get("title"),
            "category": doc.get("category"),
            "version": doc.get("version"),
            "status": doc.get("status"),
            "effective_date": doc.get("effective_date"),
            "expiry_date": doc.get("expiry_date"),
            "is_expired": is_expired,
            "created_at": doc.get("created_at"),
            "changed_by": latest_audit.get("changed_by", "admin@nexalink.com"),
            "changed_at": latest_audit.get("changed_at", doc.get("created_at")),
            "reason": latest_audit.get("reason", "Version recorded"),
            "audit_logs": doc_audits
        })

    # Sort newest first by version or created_at
    history_entries.sort(key=lambda x: x.get("version", "0"), reverse=True)

    return {
        "title": target_doc.get("title"),
        "category": target_doc.get("category"),
        "history": history_entries
    }


# ── POST Activate Draft Document ───────────────────────────────────────────────

@router.post("/{document_id}/activate")
def activate_draft_document(
    document_id: str,
    payload: ActivateDocumentRequest = Body(...),
    current_user: dict = Depends(require_role("Admin", "Administrator"))
):
    # Enforce non-empty reason string
    reason = (payload.reason or "").strip()
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Confirmation reason string is required to activate a draft document."
        )

    # Find draft document
    target_doc = None
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("document_id") == document_id:
            target_doc = doc
            break

    if not target_doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    if target_doc.get("status") == "Active":
        return {"message": "Document is already Active.", "document": target_doc}

    admin_user = current_user.get("username") or current_user.get("email") or "admin@nexalink.com"
    norm_title = _normalize(target_doc.get("title"))
    norm_category = _normalize(target_doc.get("category"))
    new_version = target_doc.get("version", "1.0")

    # Supersede any existing Active versions of the same title+category
    for doc in KNOWLEDGE_BASE_STORE:
        if (
            doc.get("document_id") != document_id
            and _normalize(doc.get("title")) == norm_title
            and _normalize(doc.get("category")) == norm_category
            and doc.get("status") == "Active"
        ):
            doc["status"] = "Superseded"
            audit_id = len(KB_VERSION_AUDIT_STORE) + 1
            KB_VERSION_AUDIT_STORE.insert(0, {
                "id": audit_id,
                "document_id": doc.get("document_id"),
                "title": doc.get("title"),
                "category": doc.get("category"),
                "previous_status": "Active",
                "new_status": "Superseded",
                "previous_version": doc.get("version"),
                "new_version": new_version,
                "changed_at": datetime.utcnow().isoformat(),
                "changed_by": admin_user,
                "reason": f"Superseded by draft activation of {document_id} ({new_version})"
            })

    # Activate target doc
    old_status = target_doc.get("status")
    target_doc["status"] = "Active"

    audit_id = len(KB_VERSION_AUDIT_STORE) + 1
    KB_VERSION_AUDIT_STORE.insert(0, {
        "id": audit_id,
        "document_id": document_id,
        "title": target_doc.get("title"),
        "category": target_doc.get("category"),
        "previous_status": old_status,
        "new_status": "Active",
        "previous_version": target_doc.get("version"),
        "new_version": target_doc.get("version"),
        "changed_at": datetime.utcnow().isoformat(),
        "changed_by": admin_user,
        "reason": reason
    })

    return {
        "message": f"Document {document_id} activated successfully.",
        "document_id": document_id,
        "status": "Active",
        "reason": reason
    }
