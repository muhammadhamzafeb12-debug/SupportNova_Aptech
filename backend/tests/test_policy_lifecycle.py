"""
Pytest Test Suite for Policy Lifecycle Management & Retrieval Rules:
1. Upload v1 as Active, upload v2 as Active (same title+category) -> v1 superseded, v2 active. History shows audit entries.
2. Retrieve chunks default (include_statuses=["Active"]) returns ONLY v2 chunks, 0 from v1 (Superseded).
3. Document past expiry_date is excluded from Active retrieval even if status="Active", logging a warning.
4. Activate endpoint rejects missing/empty reason with 422 Unprocessable Entity.
"""
import io
import time
import logging
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.src.main import app
from backend.src.store import KNOWLEDGE_BASE_STORE, KB_CHUNKS_STORE, KB_VERSION_AUDIT_STORE
from backend.document_processing.retriever import (
    add_chunks_to_index,
    retrieve_relevant_chunks,
    remove_document_chunks
)

client = TestClient(app)


def get_admin_headers():
    resp = client.post("/auth/login", json={"username": "admin@nexalink.com", "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ── Test 1: Upload v1 then v2 -> v1 superseded, v2 active, history chain correct ──

def test_upload_v2_supersedes_v1_and_history_chain():
    headers = get_admin_headers()
    title = "NexaLink Executive SLA Guideline"
    category = "policy"

    # Upload Version 1.0 (Active)
    content_v1 = b"Executive SLA Guideline Version 1.0: Guaranteed 99.9% uptime for enterprise customers."
    f1 = ("exec_sla_v1.txt", io.BytesIO(content_v1), "text/plain")
    data_v1 = {
        "title": title,
        "category": category,
        "version": "1.0",
        "effective_date": "2026-01-01"
    }

    r1 = client.post("/admin/knowledge-base/upload", headers=headers, data=data_v1, files={"file": f1})
    assert r1.status_code == 201
    doc_v1 = r1.json()
    assert doc_v1["status"] == "Active"
    doc_id_v1 = doc_v1["document_id"]

    # Upload Version 2.0 (Active)
    content_v2 = b"Executive SLA Guideline Version 2.0: Guaranteed 99.99% uptime with 4-hour priority escalation."
    f2 = ("exec_sla_v2.txt", io.BytesIO(content_v2), "text/plain")
    data_v2 = {
        "title": title,
        "category": category,
        "version": "2.0",
        "effective_date": "2026-06-01"
    }

    r2 = client.post("/admin/knowledge-base/upload", headers=headers, data=data_v2, files={"file": f2})
    assert r2.status_code == 201
    doc_v2 = r2.json()
    assert doc_v2["status"] == "Active"
    doc_id_v2 = doc_v2["document_id"]

    # Assert V1 is now Superseded
    v1_record = next(d for d in KNOWLEDGE_BASE_STORE if d["document_id"] == doc_id_v1)
    assert v1_record["status"] == "Superseded", f"Expected 'Superseded', got {v1_record['status']}"

    # Check History Endpoint
    hist_resp = client.get(f"/admin/knowledge-base/{doc_id_v2}/history", headers=headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert "history" in hist_data
    history = hist_data["history"]

    assert len(history) >= 2
    v2_entry = next(h for h in history if h["document_id"] == doc_id_v2)
    v1_entry = next(h for h in history if h["document_id"] == doc_id_v1)

    assert v2_entry["status"] == "Active"
    assert v1_entry["status"] == "Superseded"
    assert v2_entry["version"] == "2.0"
    assert v1_entry["version"] == "1.0"


# ── Test 2: Retrieval Exclusion of Superseded Chunks ─────────────────────────

def test_retrieval_excludes_superseded_chunks():
    """
    CRITICAL BUSINESS RULE: Default retrieve_relevant_chunks returns ONLY Active chunks.
    Draft and Superseded chunks must NEVER be returned by default.
    """
    doc_id_active = "KB-DOC-ACTIVE-TEST"
    doc_id_superseded = "KB-DOC-SUPERSEDED-TEST"

    # Add mock documents to store
    KNOWLEDGE_BASE_STORE.append({
        "document_id": doc_id_active,
        "title": "Network SLA 2026",
        "category": "policy",
        "status": "Active",
        "expiry_date": None
    })
    KNOWLEDGE_BASE_STORE.append({
        "document_id": doc_id_superseded,
        "title": "Network SLA 2025",
        "category": "policy",
        "status": "Superseded",
        "expiry_date": None
    })

    chunk_active = {
        "chunk_id": "chunk-active-001",
        "document_id": doc_id_active,
        "section": "Section 1",
        "heading": "Network SLA Uptime",
        "text": "Active 2026 Network SLA uptime target is 99.99% for business lines.",
        "word_count": 10
    }
    chunk_superseded = {
        "chunk_id": "chunk-superseded-001",
        "document_id": doc_id_superseded,
        "section": "Section 1",
        "heading": "Network SLA Uptime",
        "text": "Superseded 2025 Network SLA uptime target was 99.0% for business lines.",
        "word_count": 10
    }

    add_chunks_to_index([chunk_active, chunk_superseded])

    # Default retrieval (include_statuses=["Active"])
    results = retrieve_relevant_chunks("Network SLA uptime target", top_k=10)

    doc_ids_returned = [r["document_id"] for r in results]
    assert doc_id_active in doc_ids_returned, "Active document chunk should be returned"
    assert doc_id_superseded not in doc_ids_returned, "Superseded document chunk must NOT be returned by default"


# ── Test 3: Retrieval Exclusion of Expired Documents + Warning Log ─────────

def test_retrieval_excludes_expired_documents(caplog):
    """
    Documents past expiry_date must be excluded from default Active retrieval even if status='Active'.
    A warning must be logged.
    """
    doc_id_expired = "KB-DOC-EXPIRED-TEST"
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime("%Y-%m-%d")

    KNOWLEDGE_BASE_STORE.append({
        "document_id": doc_id_expired,
        "title": "Expired Promotional SOP 2025",
        "category": "SOP",
        "status": "Active",  # Status still says Active in DB
        "expiry_date": yesterday
    })

    chunk_expired = {
        "chunk_id": "chunk-expired-001",
        "document_id": doc_id_expired,
        "section": "Promo 1",
        "heading": "Expired Promo Credit",
        "text": "Expired promotional discount credit of $50 for holiday campaign.",
        "word_count": 10
    }

    add_chunks_to_index([chunk_expired])

    with caplog.at_level(logging.WARNING):
        results = retrieve_relevant_chunks("Expired promotional discount credit", top_k=5)

    doc_ids_returned = [r["document_id"] for r in results]
    assert doc_id_expired not in doc_ids_returned, "Expired document chunk must be excluded from Active retrieval"

    # Verify warning log was generated
    assert any("EXCLUDING EXPIRED DOCUMENT" in record.message for record in caplog.records), \
        "Warning log should be generated when excluding an expired document"


# ── Test 4: Activate Endpoint Rejects Missing Reason with 422 ────────────────

def test_activate_draft_requires_reason_and_succeeds():
    headers = get_admin_headers()

    # Upload Draft Document
    content = b"Draft Regulatory Policy 2026: Pending executive review."
    f = ("draft_policy.txt", io.BytesIO(content), "text/plain")
    data = {
        "title": "Draft Regulatory Policy 2026",
        "category": "policy",
        "version": "0.1",
        "effective_date": "2026-07-01",
        "is_draft": "true"
    }

    upload_resp = client.post("/admin/knowledge-base/upload", headers=headers, data=data, files={"file": f})
    assert upload_resp.status_code == 201
    doc = upload_resp.json()
    assert doc["status"] == "Draft"
    doc_id = doc["document_id"]

    # 1. Attempt to activate without reason -> expect 422 Unprocessable Entity
    r_bad = client.post(f"/admin/knowledge-base/{doc_id}/activate", headers=headers, json={"reason": ""})
    assert r_bad.status_code == 422, f"Expected 422 for empty reason, got {r_bad.status_code}"

    # 2. Activate with valid reason -> expect 200 OK
    r_good = client.post(
        f"/admin/knowledge-base/{doc_id}/activate",
        headers=headers,
        json={"reason": "Approved by Regulatory Compliance Officer Jane Doe"}
    )
    assert r_good.status_code == 200
    res_body = r_good.json()
    assert res_body["status"] == "Active"
    assert res_body["reason"] == "Approved by Regulatory Compliance Officer Jane Doe"

    # Verify status in store
    doc_rec = next(d for d in KNOWLEDGE_BASE_STORE if d["document_id"] == doc_id)
    assert doc_rec["status"] == "Active"
