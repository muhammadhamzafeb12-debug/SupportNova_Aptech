"""
Pytest Test Suite for Admin Knowledge-Base Upload Module
"""
import io
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

def get_admin_headers():
    login_resp = client.post("/auth/login", json={
        "username": "admin@nexalink.com",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_valid_kb_upload():
    headers = get_admin_headers()
    file_content = b"NexaLink Refund Policy 2026: Customers receive 100% refund for outages > 24 hours."
    file = ("nexalink_refund_policy_2026.pdf", io.BytesIO(file_content), "application/pdf")

    data = {
        "title": "NexaLink Refund Policy 2026",
        "category": "policy",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "expiry_date": "2027-01-01"
    }

    response = client.post(
        "/admin/knowledge-base/upload",
        headers=headers,
        data=data,
        files={"file": file}
    )

    assert response.status_code == 201
    res_json = response.json()
    assert res_json["title"] == "NexaLink Refund Policy 2026"
    assert res_json["status"] == "Active"
    assert "document_id" in res_json
    assert "content_hash" in res_json

def test_duplicate_kb_upload_rejection():
    headers = get_admin_headers()
    file_content = b"Unique content for duplicate test: NexaLink Network SLA v2"
    file1 = ("sla_v2.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    file2 = ("sla_v2_copy.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    data = {
        "title": "Network SLA v2",
        "category": "SOP",
        "version": "2.0",
        "effective_date": "2026-03-01"
    }

    # First upload
    res1 = client.post("/admin/knowledge-base/upload", headers=headers, data=data, files={"file": file1})
    assert res1.status_code == 201

    # Second duplicate upload
    res2 = client.post("/admin/knowledge-base/upload", headers=headers, data=data, files={"file": file2})
    assert res2.status_code == 400
    res_json = res2.json()
    assert res_json["error_code"] == "duplicate_document"

def test_unsupported_file_type_rejection():
    headers = get_admin_headers()
    file_content = b"malicious binary script content"
    file = ("script.exe", io.BytesIO(file_content), "application/octet-stream")

    data = {
        "title": "Executable File Test",
        "category": "policy",
        "version": "1.0",
        "effective_date": "2026-01-01"
    }

    response = client.post(
        "/admin/knowledge-base/upload",
        headers=headers,
        data=data,
        files={"file": file}
    )

    assert response.status_code == 400
    res_json = response.json()
    assert res_json["error_code"] == "unsupported_file_type"

def test_oversized_file_rejection():
    headers = get_admin_headers()
    # Create 21MB fake file content
    oversized_content = b"0" * (21 * 1024 * 1024)
    file = ("large_manual.pdf", io.BytesIO(oversized_content), "application/pdf")

    data = {
        "title": "Oversized Policy Manual",
        "category": "policy",
        "version": "1.0",
        "effective_date": "2026-01-01"
    }

    response = client.post(
        "/admin/knowledge-base/upload",
        headers=headers,
        data=data,
        files={"file": file}
    )

    assert response.status_code == 400
    res_json = response.json()
    assert res_json["error_code"] == "file_too_large"
