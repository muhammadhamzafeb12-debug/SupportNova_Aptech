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
    token = create_access_token({"sub": "admin@nexalink.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


# ── Acceptance Criterion 1: Deterministic Engine Match (10 Inputs, 2 Runs) ───

def test_engine_deterministic_matching_10_inputs():
    engine = RuleMatrixEngine()

    test_inputs = [
        # Input 1: Standard billing dispute
        ({"category": "Billing & Payments", "subcategory": "Incorrect Charge on Invoice", "customer_tier": "standard", "dispute_amount_max": 50.0, "business_risk_level": "low"}, "RULE-0001"),
        # Input 2: VIP billing dispute
        ({"category": "Billing & Payments", "subcategory": "Incorrect Charge on Invoice", "customer_tier": "vip", "dispute_amount_min": 150.0, "dispute_amount_max": 300.0}, "RULE-0002"),
        # Input 3: Network signal outage
        ({"category": "Network & Connectivity", "subcategory": "No Signal / Complete Outage", "customer_tier": "standard", "dispute_amount_max": 20.0, "business_risk_level": "low"}, "RULE-0010"),
        # Input 4: Device defective
        ({"category": "Device & Equipment", "subcategory": "Defective Device Received", "customer_tier": "standard", "dispute_amount_max": 80.0, "business_risk_level": "low"}, "RULE-0022"),
        # Input 5: Account login failure
        ({"category": "Account Management", "subcategory": "Unable to Access Account / Login Failure", "customer_tier": "standard", "dispute_amount_max": 0.0, "business_risk_level": "low"}, "RULE-0031"),
        # Input 6: Security SIM swap fraud
        ({"category": "Account Security & Fraud", "subcategory": "Unauthorized SIM Swap / Port-Out", "security_incident_type": "sim_swap"}, "RULE-0103"),
        # Input 7: FCC regulatory complaint
        ({"category": "Regulatory & Compliance", "subcategory": "FCC / State Regulator Referenced Complaint", "legal_regulatory_threat": True}, "RULE-0104"),
        # Input 8: Massive outage
        ({"category": "Network & Connectivity", "subcategory": "No Signal / Complete Outage", "affected_subscribers_min": 500}, "RULE-0105"),
        # Input 9: High repeat complaint escalation
        ({"category": "International Roaming", "subcategory": "Unexpected Roaming Charges", "repeat_complaints_min": 4, "unresolved_days_min": 7}, "RULE-0051"),
        # Input 10: IPTV DVR failure standard
        ({"category": "NexaStream TV & IPTV", "subcategory": "Cloud DVR Not Recording / Recordings Lost", "customer_tier": "standard", "dispute_amount_max": 10.0, "business_risk_level": "low"}, "RULE-0064"),
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
        "category": "Billing & Payments",
        "subcategory": "Promotional Discount Not Applied",
        "contains_safety_keyword": False,
        "business_risk_level": "low",
        "dispute_amount_max": 25.0,
        "sentiment_score": 0.05,  # Extremely angry / hostile sentiment
        "customer_sentiment": "furious"
    }

    matched_angry = engine.match(angry_low_risk_features)
    assert matched_angry is not None
    assert matched_angry.rule_id == "RULE-0102"
    assert matched_angry.urgency == "Low"
    assert matched_angry.priority == "Medium"
    assert matched_angry.escalation_required is False

    # Case B: Calm tone, safety keyword present -> Critical urgency & mandatory escalation
    calm_safety_features = {
        "category": "Device & Equipment",
        "subcategory": "Router / Mesh Node Malfunction",
        "contains_safety_keyword": True,
        "sentiment_score_min": 0.5,
        "sentiment_score": 0.85,  # Extremely calm, polite tone
        "customer_sentiment": "neutral_polite"
    }

    matched_calm_safety = engine.match(calm_safety_features)
    assert matched_calm_safety is not None
    assert matched_calm_safety.rule_id == "RULE-0101"
    assert matched_calm_safety.urgency == "Critical"
    assert matched_calm_safety.priority == "Urgent"
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
        "subcategory": "Incorrect Charge on Invoice",
        "conditions": {"customer_tier": "standard"},
        "department": "Billing & Revenue Assurance",
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
        "file_path": "sample_documents/NexaLink_Refund_Policy_2026.pdf",
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
    active_pol_id = "KB-DOC-1002"
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("status") == "Active":
            active_pol_id = doc.get("document_id")
            break

    # First create a valid rule
    create_payload = {
        "rule_id": "RULE-TEST-SOFTDELETE",
        "category": "Billing & Payments",
        "subcategory": "Incorrect Charge on Invoice",
        "conditions": {"test_key": "val"},
        "department": "Billing & Revenue Assurance",
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
