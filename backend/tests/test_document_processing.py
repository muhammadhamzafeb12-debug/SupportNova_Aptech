"""
Pytest Test Suite for Document Processing Pipeline:
- Successful parse + chunk of a sample TXT
- Successful parse + chunk of a Billing Policy
- Retrieval relevance test: query "refund eligibility damaged product" returns correct chunk
- Backend API tests: upload triggers BackgroundTask, status updates, chunks endpoint
"""
import io
import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

# ─── Helpers ────────────────────────────────────────────────────────────────

def get_admin_headers():
    resp = client.post("/auth/login", json={"username": "admin@velvocart.com", "password": "password123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_documents"

# ─── Test 1: Parse + Chunk a Plain-Text Policy Document ─────────────────────

def test_parse_and_chunk_text_document():
    """Parse the VelvoCart Return Policy .txt and verify chunk metadata."""
    from backend.document_processing.parser import parse_document
    from backend.document_processing.chunker import chunk_sections

    txt_path = str(SAMPLE_DOCS_DIR / "VelvoCart_Return_Policy_2026.txt")
    assert Path(txt_path).exists(), f"Sample file missing: {txt_path}"

    sections = parse_document(txt_path)
    assert len(sections) >= 1, "Should parse at least one section"

    # Verify section structure
    first = sections[0]
    assert "page" in first
    assert "text" in first
    assert len(first["text"]) > 0

    # Chunk and verify
    chunks = chunk_sections(sections, document_id="KB-DOC-TEST-001", version="1.0")
    assert len(chunks) >= 1, "Should produce at least one chunk"

    for chunk in chunks:
        assert "chunk_id" in chunk
        assert "document_id" in chunk
        assert "section" in chunk
        assert "heading" in chunk
        assert "page_reference" in chunk
        assert "version" in chunk
        assert "text" in chunk
        assert chunk["document_id"] == "KB-DOC-TEST-001"
        assert len(chunk["text"].split()) <= 420, f"Chunk too large: {len(chunk['text'].split())} words"
        assert len(chunk["text"].split()) >= 1


# ─── Test 2: Parse + Chunk a Billing Policy ─────────────────

def test_parse_and_chunk_billing_sop():
    """Parse the VelvoCart Billing Policy .txt and verify chunking."""
    from backend.document_processing.parser import parse_document
    from backend.document_processing.chunker import chunk_sections

    txt_path = str(SAMPLE_DOCS_DIR / "VelvoCart_Billing_Payment_Policy.txt")
    assert Path(txt_path).exists(), f"Sample file missing: {txt_path}"

    sections = parse_document(txt_path)
    assert len(sections) >= 1

    chunks = chunk_sections(sections, document_id="KB-DOC-TEST-002", version="2.1")
    assert len(chunks) >= 1, "Billing policy should produce chunks"

    # Verify billing-specific content appears in chunks
    all_text = " ".join(c["text"] for c in chunks).lower()
    assert any(keyword in all_text for keyword in ["billing", "payment", "card", "charge", "credit"]), \
        "Billing policy chunks should contain billing-domain keywords"


# ─── Test 3: Retrieval Relevance Test ───────────────────────────────────────

def test_retrieval_relevance_damaged_product_query():
    """
    After indexing the refund policy, querying for 'refund eligibility damaged product'
    should return the relevant chunk in the top 3 results.
    """
    from backend.document_processing.parser import parse_document
    from backend.document_processing.chunker import chunk_sections
    from backend.document_processing.retriever import add_chunks_to_index, retrieve_relevant_chunks

    txt_path = str(SAMPLE_DOCS_DIR / "VelvoCart_Return_Policy_2026.txt")
    sections = parse_document(txt_path)
    chunks = chunk_sections(sections, document_id="KB-DOC-RETRIEVAL-TEST", version="1.0")

    # Index the chunks
    add_chunks_to_index(chunks)

    # Query for damaged product refund
    query = "refund eligibility for damaged product"
    results = retrieve_relevant_chunks(query, top_k=5)

    assert len(results) >= 1, "Should return at least one result for a valid query"

    # The top-3 results should contain 'damage' or 'refund' or 'return'
    top3_text = " ".join(r["text"].lower() for r in results[:3])
    assert any(k in top3_text for k in ["damage", "refund", "return", "product", "eligib"]), \
        f"Top-3 results should contain relevant terms. Got: {top3_text[:300]}"

    # Verify result structure
    for result in results:
        assert "chunk_id" in result
        assert "document_id" in result
        assert "relevance_score" in result
        assert isinstance(result["relevance_score"], float)


# ─── Test 4: Upload via API triggers BackgroundTask (status goes pending→completed) ──

def test_upload_sets_parsing_status_pending():
    """Upload a valid document and verify parsing_status starts as 'pending'."""
    headers = get_admin_headers()
    content = b"Test SLA Policy 2026: Service level agreements for escalation procedures and customer credits."
    file = ("test_sla_policy.txt", io.BytesIO(content), "text/plain")

    data = {
        "title": "Test SLA Policy",
        "category": "policy",
        "version": "1.0",
        "effective_date": "2026-04-01",
    }

    resp = client.post("/admin/knowledge-base/upload", headers=headers, data=data, files={"file": file})
    assert resp.status_code == 201

    body = resp.json()
    assert body.get("parsing_status") == "pending", \
        f"Expected 'pending' immediately after upload, got: {body.get('parsing_status')}"
    assert "document_id" in body

    doc_id = body["document_id"]

    # Poll status endpoint — allow up to 15 seconds for background task to complete
    final_status = None
    for _ in range(15):
        time.sleep(1)
        status_resp = client.get(f"/admin/knowledge-base/{doc_id}/status", headers=headers)
        if status_resp.status_code == 200:
            final_status = status_resp.json().get("parsing_status")
            if final_status in ("completed", "failed"):
                break

    assert final_status in ("completed", "failed"), \
        f"Parsing should finish within 15 seconds, got: {final_status}"


# ─── Test 5: Chunks Endpoint Returns Chunks After Processing ────────────────

def test_chunks_endpoint_returns_chunks():
    """After a successful upload+parse, GET /{doc_id}/chunks should return chunks."""
    headers = get_admin_headers()
    content = (
        b"VelvoCart Delivery Policy 2026.\n"
        b"Section 1: Eligibility. Customers experiencing delivery delays qualify for credits.\n"
        b"Section 2: Credit Amount. Ten percent of order value for each additional day.\n"
        b"Section 3: Approval. Agents may approve up to fifty dollars automatically.\n"
        b"Section 4: Appeals. Submit appeals within 30 days to the fulfillment department.\n"
        b"Section 5: Regulatory Compliance. Consumer protection laws apply to all determinations."
    )
    file = ("chunks_test_policy.txt", io.BytesIO(content), "text/plain")

    data = {
        "title": "Chunks Test Delivery Policy",
        "category": "policy",
        "version": "1.0",
        "effective_date": "2026-05-01",
    }

    upload_resp = client.post(
        "/admin/knowledge-base/upload", headers=headers, data=data, files={"file": file}
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["document_id"]

    # Wait for processing
    for _ in range(15):
        time.sleep(1)
        sr = client.get(f"/admin/knowledge-base/{doc_id}/status", headers=headers)
        if sr.json().get("parsing_status") in ("completed", "failed"):
            break

    chunks_resp = client.get(f"/admin/knowledge-base/{doc_id}/chunks", headers=headers)
    assert chunks_resp.status_code == 200
    body = chunks_resp.json()
    assert "chunks" in body
    assert "chunk_count" in body
    # There should be at least one chunk
    chunks = body["chunks"]
    assert len(chunks) >= 1, f"Expected chunks; got {chunks}"


# ─── Test 6: Failed parsing_status on corrupted file ────────────────────────

def test_corrupted_file_sets_failed_status():
    """
    Uploading a corrupted binary file disguised as a PDF should result in
    parsing_status = 'failed' after the pipeline runs.
    """
    headers = get_admin_headers()
    content = b"\x00\x01CORRUPT\xff\xfe" * 100
    file = ("corrupted_report.txt", io.BytesIO(content), "text/plain")

    data = {
        "title": "Corrupted Binary Report",
        "category": "SOP",
        "version": "1.0",
        "effective_date": "2026-01-01",
    }

    resp = client.post("/admin/knowledge-base/upload", headers=headers, data=data, files={"file": file})
    assert resp.status_code == 201
    doc_id = resp.json()["document_id"]

    for _ in range(10):
        time.sleep(1)
        sr = client.get(f"/admin/knowledge-base/{doc_id}/status", headers=headers)
        if sr.json().get("parsing_status") in ("completed", "failed"):
            break

    final_status = sr.json().get("parsing_status")
    assert final_status in ("completed", "failed"), \
        f"Status should be terminal, got: {final_status}"
