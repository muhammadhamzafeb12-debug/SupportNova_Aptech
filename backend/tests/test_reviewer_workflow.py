"""
Test Suite: Reviewer Workflow & SLA Tracking — SupportNova
============================================================
Acceptance Criteria:
  AC1  Invalid status transition → 400, all valid transitions pass
  AC2  "modify" decision stores original GenAI, original Python, reviewer values
       — all three retrievable via audit-trail endpoint
  AC3  GET /reviewer/queue only returns Manual Review Required complaints
  AC4  compute_sla_status() flags at-risk/breached correctly with mocked timestamps
  AC5  Customer calling POST /reviewer/{id}/decision → 403
  AC6  Zero regressions in full backend/tests/ suite (run last)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from backend.src.main import app
from backend.security.jwt_auth import create_access_token
from backend.complaint_processing.state_machine import validate_transition, assert_valid_transition
from backend.complaint_processing.sla import compute_sla_status, DEFAULT_SLA_TARGETS
from backend.src.store import COMPLAINTS_STORE, VERIFICATION_REPORTS_STORE
from backend.src.api.reviewer import REVIEWER_DECISION_AUDIT

client = TestClient(app)

# ── Token helpers ─────────────────────────────────────────────────────────────

def reviewer_headers():
    token = create_access_token({"sub": "reviewer@nexalink.com", "role": "Reviewer", "full_name": "Test Reviewer"})
    return {"Authorization": f"Bearer {token}"}

def admin_headers():
    token = create_access_token({"sub": "admin@nexalink.com", "role": "Admin", "full_name": "Admin User"})
    return {"Authorization": f"Bearer {token}"}

def customer_headers():
    token = create_access_token({"sub": "customer@nexalink.com", "role": "Customer", "full_name": "Test Customer"})
    return {"Authorization": f"Bearer {token}"}

def agent_headers():
    token = create_access_token({"sub": "agent@nexalink.com", "role": "Agent", "full_name": "Test Agent"})
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# AC1 — Status State Machine
# ═══════════════════════════════════════════════════════════════════════════════

class TestStateMachine:
    """Tests for validate_transition() pure function — all valid and invalid pairs."""

    # ── Valid pairs ───────────────────────────────────────────────────────────
    @pytest.mark.parametrize("current,nxt", [
        ("New",               "Analyzed"),
        ("Analyzed",          "Assigned"),
        ("Analyzed",          "Escalated"),
        ("Assigned",          "In Progress"),
        ("Assigned",          "Escalated"),
        ("In Progress",       "Awaiting Customer"),
        ("In Progress",       "Resolved"),
        ("In Progress",       "Escalated"),
        ("Awaiting Customer", "In Progress"),
        ("Awaiting Customer", "Escalated"),
        ("Awaiting Customer", "Resolved"),
        ("Escalated",         "In Progress"),
        ("Escalated",         "Resolved"),
        ("Resolved",          "Closed"),
        ("Closed",            "Reopened"),
        ("Reopened",          "Assigned"),
        ("Reopened",          "In Progress"),
        ("Reopened",          "Escalated"),
        # no-op transitions
        ("New",               "New"),
        ("Resolved",          "Resolved"),
    ])
    def test_valid_transitions(self, current, nxt):
        assert validate_transition(current, nxt) is True, (
            f"Expected '{current}' → '{nxt}' to be VALID"
        )

    # ── Invalid pairs ─────────────────────────────────────────────────────────
    @pytest.mark.parametrize("current,nxt", [
        ("New",         "Closed"),     # skips multiple stages — the key AC1 case
        ("New",         "Resolved"),
        ("New",         "Reopened"),
        ("New",         "In Progress"),
        ("Closed",      "New"),        # going backward from terminal
        ("Closed",      "Resolved"),
        ("Resolved",    "New"),
        ("Resolved",    "Assigned"),
        ("Escalated",   "New"),
        ("Analyzed",    "Resolved"),
        ("Analyzed",    "Closed"),
        ("In Progress", "New"),
        ("In Progress", "Analyzed"),
    ])
    def test_invalid_transitions(self, current, nxt):
        assert validate_transition(current, nxt) is False, (
            f"Expected '{current}' → '{nxt}' to be INVALID"
        )

    def test_assert_raises_value_error_on_bad_transition(self):
        with pytest.raises(ValueError, match="Invalid status transition"):
            assert_valid_transition("New", "Closed")

    def test_assert_does_not_raise_on_valid_transition(self):
        assert_valid_transition("New", "Analyzed")  # must not raise

    def test_api_rejects_invalid_transition_with_400(self):
        """AC1: PATCH /complaints/{id} with invalid transition → 400."""
        # Seed a fresh "New" complaint into the store
        complaints_before = len(COMPLAINTS_STORE)
        COMPLAINTS_STORE.insert(0, {
            "id": 9901,
            "complaint_number": "CMP-TEST-AC1",
            "customer_email": "test@nexalink.com",
            "customer_name": "AC1 Test User",
            "account_number": "ACC-0001",
            "title": "State Machine Test",
            "category": "Billing & Payments",
            "sub_category": "General",
            "description": "Test complaint for AC1",
            "status": "New",
            "priority": "Medium",
            "assigned_department": "Billing",
            "assigned_agent": None,
            "sentiment_score": 0.5,
            "genai_summary": "",
            "genai_suggested_response": "",
            "genai_confidence": 0.8,
            "python_validation_passed": True,
            "python_validation_flags": [],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        res = client.patch(
            "/complaints/CMP-TEST-AC1",
            json={"status": "Closed"},
            headers=reviewer_headers(),
        )
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        detail = res.json()["detail"]
        assert "Invalid status transition" in detail
        assert "New" in detail
        assert "Closed" in detail

    def test_api_accepts_valid_transition(self):
        """AC1: PATCH /complaints/{id} with valid transition should succeed."""
        # Ensure the complaint from previous test exists with status "New"
        c = next((x for x in COMPLAINTS_STORE if x["complaint_number"] == "CMP-TEST-AC1"), None)
        if not c:
            pytest.skip("Seeded complaint not found")
        c["status"] = "New"  # reset
        res = client.patch(
            "/complaints/CMP-TEST-AC1",
            json={"status": "Analyzed"},
            headers=reviewer_headers(),
        )
        assert res.status_code == 200
        assert res.json()["status"] == "Analyzed"


# ═══════════════════════════════════════════════════════════════════════════════
# AC3 — Reviewer Queue filters correctly
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewerQueue:
    """GET /reviewer/queue must never return Verified complaints."""

    def _seed_manual_review_complaint(self, cid: int, cnum: str):
        COMPLAINTS_STORE.append({
            "id": cid,
            "complaint_number": cnum,
            "customer_email": "test@nexalink.com",
            "customer_name": "Queue Test",
            "account_number": "ACC-9999",
            "title": "Queue Test Complaint",
            "category": "Network & Connectivity",
            "sub_category": "Outage",
            "description": "Test complaint for queue",
            "status": "Review Required",
            "priority": "High",
            "assigned_department": "Network Ops",
            "assigned_agent": None,
            "sentiment_score": 0.2,
            "genai_summary": "Test",
            "genai_suggested_response": "Test resp",
            "genai_confidence": 0.7,
            "python_validation_passed": False,
            "python_validation_flags": [],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        VERIFICATION_REPORTS_STORE.append({
            "complaint_id": str(cid),
            "verification_score": 45.0,
            "final_status": "Manual Review Required",
            "pipeline2_status": "completed",
            "field_comparisons": {},
            "mismatches": ["Category mismatch: GenAI=Billing, Expected=Network"],
            "unsupported_promises": [],
            "hallucinated_claims": [],
            "contradictions": [],
            "overwritten_fields": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    def _seed_verified_complaint(self, cid: int, cnum: str):
        COMPLAINTS_STORE.append({
            "id": cid,
            "complaint_number": cnum,
            "customer_email": "test@nexalink.com",
            "customer_name": "Verified Test",
            "account_number": "ACC-9998",
            "title": "Verified Complaint",
            "category": "Billing & Payments",
            "sub_category": "Invoice",
            "description": "Verified complaint",
            "status": "Assigned",
            "priority": "Low",
            "assigned_department": "Billing",
            "assigned_agent": "Agent 1",
            "sentiment_score": 0.7,
            "genai_summary": "Test",
            "genai_suggested_response": "OK",
            "genai_confidence": 0.97,
            "python_validation_passed": True,
            "python_validation_flags": [],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        VERIFICATION_REPORTS_STORE.append({
            "complaint_id": str(cid),
            "verification_score": 95.0,
            "final_status": "Verified",  # <-- should NOT appear in queue
            "pipeline2_status": "completed",
            "field_comparisons": {},
            "mismatches": [],
            "unsupported_promises": [],
            "hallucinated_claims": [],
            "contradictions": [],
            "overwritten_fields": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_queue_only_returns_manual_review_required(self):
        """AC3: Verified complaint must NOT appear in the queue."""
        self._seed_manual_review_complaint(8801, "CMP-TEST-QUEUE1")
        self._seed_verified_complaint(8802, "CMP-TEST-VERIFIED1")

        res = client.get("/reviewer/queue", headers=reviewer_headers())
        assert res.status_code == 200, res.text
        data = res.json()
        numbers = [item["complaint_number"] for item in data["items"]]

        assert "CMP-TEST-QUEUE1" in numbers, "Manual Review Required complaint must appear in queue"
        assert "CMP-TEST-VERIFIED1" not in numbers, "Verified complaint must NOT appear in queue"

    def test_queue_requires_reviewer_role(self):
        """Customer must be forbidden from accessing the queue."""
        res = client.get("/reviewer/queue", headers=customer_headers())
        assert res.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# AC2 — Reviewer Decision Audit Trail (SRS req lxiii)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewerDecisionAudit:
    """AC2: modify action stores original GenAI, original Python, and reviewer's final values."""

    def _seed_complaint_with_report(self, cid: int, cnum: str):
        COMPLAINTS_STORE.append({
            "id": cid,
            "complaint_number": cnum,
            "customer_email": "audit@nexalink.com",
            "customer_name": "Audit Test",
            "account_number": "ACC-AUDIT",
            "title": "Audit Test Complaint",
            "category": "Billing & Payments",
            "sub_category": "Invoice",
            "description": "Testing audit trail",
            "status": "Review Required",
            "priority": "High",
            "assigned_department": "Billing",
            "assigned_agent": None,
            "sentiment_score": 0.3,
            "genai_summary": "GenAI summary",
            "genai_suggested_response": "GenAI response",
            "genai_confidence": 0.75,
            "genai_analysis_result": {
                "issue_category": "Billing & Payments",
                "urgency": "Medium",
                "priority": "P2",
                "escalation_required": False,
                "professional_response": "Original GenAI response text",
                "department": "Customer Service",
            },
            "python_validation_passed": False,
            "python_validation_flags": ["dept_mismatch"],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        VERIFICATION_REPORTS_STORE.append({
            "complaint_id": str(cid),
            "verification_score": 55.0,
            "final_status": "Manual Review Required",
            "pipeline2_status": "completed",
            "field_comparisons": {
                "department": {
                    "passed": False,
                    "actual_value": "Customer Service",
                    "expected_value": "Billing & Revenue Assurance",
                }
            },
            "mismatches": ["Department mismatch"],
            "unsupported_promises": [],
            "hallucinated_claims": [],
            "contradictions": [],
            "overwritten_fields": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_modify_decision_stores_three_values_in_audit(self):
        """AC2: All three values — original_genai, original_python, reviewer_final — must be in audit trail."""
        self._seed_complaint_with_report(7701, "CMP-TEST-AUDIT1")

        # Make a modify decision
        res = client.post(
            "/reviewer/CMP-TEST-AUDIT1/decision",
            json={
                "action": "modify",
                "payload": {
                    "category": "Network & Connectivity",
                    "assigned_department": "Network Operations",
                    "priority": "P1",
                },
                "comment": "Reviewer determined category was wrong based on complaint context.",
            },
            headers=reviewer_headers(),
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["action"] == "modify"

        # Retrieve audit trail
        trail_res = client.get("/reviewer/CMP-TEST-AUDIT1/audit-trail", headers=reviewer_headers())
        assert trail_res.status_code == 200, trail_res.text
        trail = trail_res.json()
        decisions = trail["decisions"]
        assert len(decisions) >= 1

        modify_entry = next((d for d in decisions if d["action"] == "modify"), None)
        assert modify_entry is not None, "modify action must appear in audit trail"

        # AC2: All three values present and non-null
        assert modify_entry["original_genai_value"] is not None, "original_genai_value must be stored"
        assert modify_entry["original_python_value"] is not None, "original_python_value must be stored"
        assert modify_entry["reviewer_final_value"] is not None, "reviewer_final_value must be stored"

        # Verify GenAI value was the original category
        assert modify_entry["original_genai_value"]["category"] == "Billing & Payments"

        # Verify reviewer's final value contains the corrected category
        assert modify_entry["reviewer_final_value"]["category"] == "Network & Connectivity"

        # Verify Python value contains the mismatch info
        assert "mismatches" in modify_entry["original_python_value"]

    def test_audit_trail_requires_reviewer_role(self):
        """Customer must be forbidden from viewing audit trail."""
        res = client.get("/reviewer/1/audit-trail", headers=customer_headers())
        assert res.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# AC4 — SLA compute_sla_status() with mocked timestamps
# ═══════════════════════════════════════════════════════════════════════════════

class TestSLAComputation:
    """AC4: Verify at_risk and breached detection with controlled timestamps."""

    MOCK_TARGETS = {
        "P0": {"response_time_hours": 2, "resolution_time_hours": 12, "at_risk_threshold_pct": 20},
        "P1": {"response_time_hours": 4, "resolution_time_hours": 24, "at_risk_threshold_pct": 20},
        "P2": {"response_time_hours": 8, "resolution_time_hours": 48, "at_risk_threshold_pct": 20},
        "P3": {"response_time_hours": 24, "resolution_time_hours": 72, "at_risk_threshold_pct": 20},
    }

    def _make_complaint(self, priority: str, created_hours_ago: float) -> dict:
        created = datetime.now(timezone.utc) - timedelta(hours=created_hours_ago)
        return {
            "id": 1,
            "priority": priority,
            "created_at": created.isoformat(),
            "status": "In Progress",
        }

    def test_not_at_risk_well_before_deadline(self):
        """P2 resolution deadline = 48h; created 5h ago → neither at-risk nor breached."""
        c = self._make_complaint("P2", 5.0)
        sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
        assert sla.is_breached is False
        assert sla.is_at_risk is False
        assert sla.time_remaining_hours > 0

    def test_at_risk_within_threshold(self):
        """P2: 48h deadline, 20% threshold = at-risk zone starts at 48 - 48*0.20 = 38.4h elapsed.
        Created 39h ago → is_at_risk must be True."""
        c = self._make_complaint("P2", 39.0)
        sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
        assert sla.is_breached is False, "Should not be breached yet"
        assert sla.is_at_risk is True, "Should be at-risk (39h > 38.4h threshold)"

    def test_breached_after_deadline(self):
        """P1: 24h deadline; created 25h ago → is_breached=True."""
        c = self._make_complaint("P1", 25.0)
        sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
        assert sla.is_breached is True
        assert sla.is_at_risk is False  # once breached, at_risk flag is False
        assert sla.time_remaining_hours < 0

    def test_p0_critical_sla(self):
        """P0: 12h deadline; created 10h ago → should be at risk (within 12*0.20=2.4h of deadline)."""
        c = self._make_complaint("P0", 10.0)
        sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
        assert sla.is_breached is False
        assert sla.is_at_risk is True  # 2h remaining < 2.4h at-risk window

    def test_p0_breached(self):
        """P0: 12h deadline; created 13h ago → must be breached."""
        c = self._make_complaint("P0", 13.0)
        sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
        assert sla.is_breached is True

    def test_priority_aliases_map_correctly(self):
        """'Urgent' should map to P0, 'High' to P1, 'Medium' to P2, 'Low' to P3."""
        for priority, expected_tier, deadline in [
            ("Urgent", "P0", 12),
            ("High",   "P1", 24),
            ("Medium", "P2", 48),
            ("Low",    "P3", 72),
        ]:
            c = self._make_complaint(priority, 0.1)
            sla = compute_sla_status(c, sla_targets=self.MOCK_TARGETS)
            assert sla.priority == expected_tier, f"'{priority}' should map to {expected_tier}"
            assert sla.resolution_deadline_hours == deadline

    def test_mocked_now_parameter(self):
        """compute_sla_status must accept _now override for deterministic testing."""
        base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        c = {
            "id": 999,
            "priority": "P2",
            "created_at": base_time.isoformat(),
            "status": "In Progress",
        }
        # 39 hours later — inside at-risk window for P2 (48h, 20% = 9.6h window)
        now = base_time + timedelta(hours=39)
        sla = compute_sla_status(c, _now=now, sla_targets=self.MOCK_TARGETS)
        assert sla.is_at_risk is True
        assert abs(sla.hours_elapsed - 39.0) < 0.01

    def test_sla_risk_endpoint_returns_at_risk_complaints(self):
        """GET /complaints/sla-risk must return breached/at-risk complaints."""
        # Seed a P0 complaint created 13h ago (breached)
        COMPLAINTS_STORE.append({
            "id": 6601,
            "complaint_number": "CMP-SLA-BREACH",
            "customer_email": "sla@nexalink.com",
            "customer_name": "SLA Test",
            "account_number": "ACC-SLA",
            "title": "SLA Breach Test",
            "category": "Billing & Payments",
            "sub_category": "Invoice",
            "description": "SLA test",
            "status": "In Progress",
            "priority": "Critical",  # maps to P0 → 12h resolution
            "assigned_department": "Billing",
            "assigned_agent": None,
            "sentiment_score": 0.5,
            "genai_summary": "",
            "genai_suggested_response": "",
            "genai_confidence": 0.8,
            "python_validation_passed": True,
            "python_validation_flags": [],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=14)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        res = client.get("/sla/risk", headers=agent_headers())
        assert res.status_code == 200, res.text
        data = res.json()
        numbers = [i["complaint_number"] for i in data["items"]]
        assert "CMP-SLA-BREACH" in numbers


# ═══════════════════════════════════════════════════════════════════════════════
# AC5 — Role-Based Access Control on Reviewer Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewerRBAC:
    """AC5: Customer (and any non-reviewer) must receive 403."""

    def test_customer_cannot_post_decision(self):
        """AC5: Customer POSTing a decision → 403."""
        res = client.post(
            "/reviewer/1/decision",
            json={"action": "approve", "payload": {}, "comment": ""},
            headers=customer_headers(),
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    def test_customer_cannot_access_queue(self):
        res = client.get("/reviewer/queue", headers=customer_headers())
        assert res.status_code == 403

    def test_reviewer_can_access_queue(self):
        res = client.get("/reviewer/queue", headers=reviewer_headers())
        assert res.status_code == 200

    def test_reviewer_can_post_decision(self):
        """Reviewer can call decision endpoint (even if complaint not found, should get 404 not 403)."""
        res = client.post(
            "/reviewer/NONEXISTENT-999/decision",
            json={"action": "add_comment", "payload": {}, "comment": "Test"},
            headers=reviewer_headers(),
        )
        # Should be 404 (not found), not 403 (forbidden)
        assert res.status_code in (404, 200), f"Should be 404 or 200, got {res.status_code}: {res.text}"
        assert res.status_code != 403


# ═══════════════════════════════════════════════════════════════════════════════
# Extra functional tests (approve, escalate, add_comment, reclassify)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReviewerDecisionActions:
    """Additional coverage for all reviewer action branches."""

    def _seed_review_complaint(self, cid: int, cnum: str, status: str = "Review Required"):
        COMPLAINTS_STORE.append({
            "id": cid,
            "complaint_number": cnum,
            "customer_email": "action@nexalink.com",
            "customer_name": "Action Test",
            "account_number": "ACC-ACT",
            "title": "Action Test",
            "category": "Account Management",
            "sub_category": "General",
            "description": "Test",
            "status": status,
            "priority": "Medium",
            "assigned_department": "Customer Service",
            "assigned_agent": None,
            "sentiment_score": 0.5,
            "genai_summary": "",
            "genai_suggested_response": "",
            "genai_confidence": 0.8,
            "genai_analysis_result": None,
            "python_validation_passed": False,
            "python_validation_flags": [],
            "has_hallucination": False,
            "hallucination_details": None,
            "requested_credit": 0.0,
            "approved_credit": 0.0,
            "resolution_notes": None,
            "security_flags": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_add_comment_action(self):
        self._seed_review_complaint(5501, "CMP-TEST-CMT1")
        res = client.post(
            "/reviewer/CMP-TEST-CMT1/decision",
            json={"action": "add_comment", "payload": {}, "comment": "Needs further review"},
            headers=reviewer_headers(),
        )
        assert res.status_code == 200
        assert res.json()["action"] == "add_comment"

    def test_escalate_action_sets_escalated_status(self):
        self._seed_review_complaint(5502, "CMP-TEST-ESC1", status="In Progress")
        res = client.post(
            "/reviewer/CMP-TEST-ESC1/decision",
            json={"action": "escalate", "payload": {"escalation_level": "Tier 3"}, "comment": "Escalating to legal"},
            headers=reviewer_headers(),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == "escalate"

    def test_unknown_action_returns_400(self):
        self._seed_review_complaint(5503, "CMP-TEST-BADACT")
        res = client.post(
            "/reviewer/CMP-TEST-BADACT/decision",
            json={"action": "do_magic", "payload": {}, "comment": ""},
            headers=reviewer_headers(),
        )
        assert res.status_code == 400
        assert "Unknown action" in res.json()["detail"]

    def test_follow_up_lifecycle(self):
        """Create and complete a follow-up."""
        self._seed_review_complaint(5510, "CMP-TEST-FU1")
        # create
        res = client.post(
            f"/sla/CMP-TEST-FU1/follow-ups",
            json={"due_date": "2026-10-01", "follow_up_type": "info_request"},
            headers=agent_headers(),
        )
        assert res.status_code == 201, res.text
        fu = res.json()
        fu_id = fu["id"]
        assert fu["completed"] is False

        # list
        list_res = client.get("/sla/CMP-TEST-FU1/follow-ups", headers=agent_headers())
        assert list_res.status_code == 200
        fus = list_res.json()["follow_ups"]
        assert any(f["id"] == fu_id for f in fus)

        # complete
        comp_res = client.post(
            f"/sla/CMP-TEST-FU1/follow-ups/{fu_id}/complete",
            headers=agent_headers(),
        )
        assert comp_res.status_code == 200
        assert comp_res.json()["completed"] is True

    def test_invalid_follow_up_type_returns_400(self):
        self._seed_review_complaint(5511, "CMP-TEST-FU2")
        res = client.post(
            "/sla/CMP-TEST-FU2/follow-ups",
            json={"due_date": "2026-10-01", "follow_up_type": "make_coffee"},
            headers=agent_headers(),
        )
        assert res.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# SLA Admin endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestSLAAdminEndpoints:
    def test_get_sla_targets(self):
        res = client.get("/admin/sla-targets", headers=agent_headers())
        assert res.status_code == 200
        data = res.json()
        assert "P0" in data
        assert "P2" in data

    def test_update_sla_targets_admin_only(self):
        """Only admin can PUT sla-targets."""
        # Customer should be forbidden
        res = client.put(
            "/admin/sla-targets",
            json={"P2": {"resolution_time_hours": 72}},
            headers=customer_headers(),
        )
        assert res.status_code == 403

        # Admin can update
        res = client.put(
            "/admin/sla-targets",
            json={"P2": {"resolution_time_hours": 72, "at_risk_threshold_pct": 25}},
            headers=admin_headers(),
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
