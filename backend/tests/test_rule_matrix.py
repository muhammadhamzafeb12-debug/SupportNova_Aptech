"""
Comprehensive Test Suite for Complaint Resolution Rule Matrix & RuleMatrixEngine
Verifies determinism, sentiment-vs-urgency trap, policy status validation, soft-delete, audit trails, and SRS seed minimums.
"""
import pytest
from fastapi.testclient import TestClient
from backend.src.main import app
from backend.complaint_rules.engine import RuleMatrixEngine
from backend.src.store import RULE_MATRIX_STORE, KNOWLEDGE_BASE_STORE, RULE_MATRIX_AUDIT_STORE
from backend.security.jwt_auth import create_access_token

client = TestClient(app)

# Helper token generator
def get_admin_headers():
    token = create_access_token({"sub": "admin@velvocart.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


# ── Acceptance Criterion 1: Deterministic Engine Match (10 Inputs, 2 Runs) ───

def test_engine_deterministic_matching_10_inputs():
    engine = RuleMatrixEngine()

    test_inputs = [
        # Input 1: Standard billing dispute
        ({"category": "Billing & Payments", "subcategory": "Duplicate Payment Deducted", "dispute_amount_max": 50.0}, "RULE-0001"),
        # Input 2: Returns denied dispute
        ({"category": "Returns & Refunds", "subcategory": "Return Request Denied"}, "RULE-0002"),
        # Input 3: Order delayed
        ({"category": "Order & Delivery", "subcategory": "Delayed Delivery"}, "RULE-0003"),
        # Input 4: Product defective
        ({"category": "Product Quality & Authenticity", "subcategory": "Defective or Malfunctioning Product"}, "RULE-0004"),
        # Input 5: Account login failure
        ({"category": "Account Management", "subcategory": "Unable to Login / Password Reset Error"}, "RULE-0005"),
        # Input 6: Security unauthorized purchase
        ({"category": "Account Security & Fraud", "subcategory": "Unauthorized Order / Credit Card Fraud"}, "RULE-0006"),
        # Input 7: Data privacy violation
        ({"category": "Regulatory & Legal Compliance", "subcategory": "Data Privacy Law Violation"}, "RULE-0007"),
        # Input 8: Marketplace seller dispute
        ({"category": "Marketplace & Seller Operations", "subcategory": "3rd-Party Seller Non-Response"}, "RULE-0008"),
        # Input 9: Customer service rude agent
        ({"category": "Customer Service Experience", "subcategory": "Unprofessional Agent Conduct"}, "RULE-0009"),
        # Input 10: Promo coupon rejected
        ({"category": "Promotions & Pricing", "subcategory": "Promo Code / Discount Rejected"}, "RULE-0010"),
    ]

    # First Run
    run_1_results = []
    for features, _ in test_inputs:
        matched = engine.match(features)
        assert matched is not None, f"Failed to match features: {features}"
        run_1_results.append(matched.rule_id)

    # Second Run (proving 100% determinism)
    run_2_results = []
    for features, _ in test_inputs:
        matched = engine.match(features)
        assert matched is not None
        run_2_results.append(matched.rule_id)

    # Assert exact 1:1 match across runs
    assert run_1_results == run_2_results, "Engine output was not 100% deterministic between runs!"


# ── Acceptance Criterion 2: Sentiment-vs-Urgency Trap Test ────────────────────

def test_sentiment_vs_urgency_trap():
    engine = RuleMatrixEngine()

    # Case A: Angry tone, no safety keyword, low business risk -> Low/Medium priority
    angry_low_risk_features = {
        "category": "Promotions & Pricing",
        "subcategory": "Promo Code / Discount Rejected",
        "contains_safety_keyword": False,
        "business_risk_level": "low",
        "dispute_amount_max": 5.0,
        "sentiment_score": 0.05,  # Extremely angry / hostile sentiment
        "customer_sentiment": "furious"
    }

    matched_angry = engine.match(angry_low_risk_features)
    assert matched_angry is not None
    assert matched_angry.urgency in ("Low", "Medium")
    assert matched_angry.escalation_required is False

    # Case B: Calm tone, safety keyword present -> Critical urgency & mandatory escalation
    calm_safety_features = {
        "category": "Product Quality & Authenticity",
        "subcategory": "Defective or Malfunctioning Product",
        "contains_safety_keyword": True,
        "sentiment_score": 0.85,  # Extremely calm, polite tone
        "customer_sentiment": "neutral_polite"
    }

    matched_calm_safety = engine.match(calm_safety_features)
    assert matched_calm_safety is not None
    assert matched_calm_safety.urgency in ("Critical", "High")
    assert matched_calm_safety.escalation_required is True


# ── Acceptance Criterion 3: Policy ID Status Validation (Draft/Superseded Rejected)

def test_create_rule_validates_active_policy_status():
    headers = get_admin_headers()

    # Ensure a Draft document exists
    draft_doc_id = "KB-DOC-DRAFT-TEST"
    KNOWLEDGE_BASE_STORE.append({
        "document_id": draft_doc_id,
        "title": "Staging Draft Policy",
        "category": "policy",
        "version": "1.0-draft",
        "status": "Draft",
        "effective_date": "2026-10-01",
        "file_name": "draft.txt",
        "file_path": "sample_documents/draft_policy.txt",
        "content_hash": "hash_draft_123"
    })

    # Attempt to create rule referencing Draft policy
    payload = {
        "rule_id": "RULE-FAIL-DRAFT",
        "category": "Billing & Payments",
        "subcategory": "Duplicate Payment Deducted",
        "conditions": {"customer_tier": "standard"},
        "department": "Billing & Payment Operations",
        "urgency": "Medium",
        "priority": "Medium",
        "policy_id": draft_doc_id,
        "escalation_required": False
    }

    res = client.post("/admin/rule-matrix", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Draft" in res.json()["detail"]

    # Ensure a Superseded document exists
    superseded_doc_id = "KB-DOC-SUPERSEDED-TEST"
    KNOWLEDGE_BASE_STORE.append({
        "document_id": superseded_doc_id,
        "title": "Old Policy 2025",
        "category": "policy",
        "version": "0.9",
        "status": "Superseded",
        "effective_date": "2025-01-01",
        "file_name": "old_policy.pdf",
        "file_path": "sample_documents/VelvoCart_Return_Policy_2026.txt",
        "content_hash": "hash_old_456"
    })

    # Attempt to create rule referencing Superseded policy
    payload["policy_id"] = superseded_doc_id
    payload["rule_id"] = "RULE-FAIL-SUPERSEDED"

    res = client.post("/admin/rule-matrix", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Superseded" in res.json()["detail"]


# ── Acceptance Criterion 4: Soft Delete is_active=False & Audit Trail Log ──────

def test_soft_delete_and_audit_log():
    headers = get_admin_headers()

    # Find an active policy ID dynamically
    active_pol_id = "KB-DOC-1001"
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("status") == "Active":
            active_pol_id = doc.get("document_id")
            break

    # First create a valid rule
    create_payload = {
        "rule_id": "RULE-TEST-SOFTDELETE",
        "category": "Billing & Payments",
        "subcategory": "Duplicate Payment Deducted",
        "conditions": {"test_key": "val"},
        "department": "Billing & Payment Operations",
        "urgency": "Low",
        "priority": "Low",
        "policy_id": active_pol_id,
        "escalation_required": False
    }

    res_create = client.post("/admin/rule-matrix", json=create_payload, headers=headers)
    assert res_create.status_code == 201

    # Soft delete rule
    res_del = client.delete("/admin/rule-matrix/RULE-TEST-SOFTDELETE", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["is_active"] is False

    # Verify rule is not in default active list
    res_list = client.get("/admin/rule-matrix", headers=headers)
    active_ids = [r["rule_id"] for r in res_list.json()["items"]]
    assert "RULE-TEST-SOFTDELETE" not in active_ids

    # Verify audit log endpoint STILL returns audit chain for soft-deleted rule
    res_audit = client.get("/admin/rule-matrix/RULE-TEST-SOFTDELETE/audit-log", headers=headers)
    assert res_audit.status_code == 200
    audit_chain = res_audit.json()
    assert len(audit_chain) >= 2  # CREATE and DEACTIVATE entries
    actions = [a["action"] for a in audit_chain]
    assert "CREATE" in actions
    assert "DEACTIVATE" in actions


# ── Acceptance Criterion 5: Seed Count Minimums (>=100 Total, >=30 Escalation) ─

def test_seed_rule_matrix_srs_minimums():
    total_active = sum(1 for r in RULE_MATRIX_STORE if r.get("is_active", True))
    escalation_active = sum(1 for r in RULE_MATRIX_STORE if r.get("is_active", True) and r.get("escalation_required"))

    print(f"Total Active Seeded Rules: {total_active}")
    print(f"Total Escalation Required Seeded Rules: {escalation_active}")

    assert total_active >= 100, f"SRS Violation: Expected >= 100 rules, found {total_active}"
    assert escalation_active >= 30, f"SRS Violation: Expected >= 30 escalation rules, found {escalation_active}"
