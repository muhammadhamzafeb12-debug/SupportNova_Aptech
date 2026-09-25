"""
Comprehensive Test Suite for Pipeline 2 — Python Ground-Truth Validation Pipeline + Comparison Engine.
Covers all 12 independent validators, schema pre-check, critical precedence overrides, and acceptance criteria.
"""
import pytest
from unittest.mock import MagicMock, patch

from backend.python_validation.validators import (
    validate_category,
    validate_department_routing,
    validate_urgency,
    validate_escalation,
    validate_policy_applicability,
    validate_resolution_steps,
    validate_refund_eligibility,
    validate_replacement_eligibility,
    validate_compensation,
    detect_unsupported_promises,
    detect_hallucinated_claims,
    detect_contradictory_instructions,
    ValidationOutcome
)
from backend.python_validation.schema_check import pre_check_schema
from backend.comparison_engine.engine import compare_and_verify
from backend.complaint_rules.engine import RuleMatrixEngine


# ── FIXTURES & HELPERS ────────────────────────────────────────────────────────

@pytest.fixture
def valid_genai_result():
    return {
        "complaint_id": "9001",
        "primary_issue": "Fiber internet outage lasting 48 hours",
        "secondary_issues": [],
        "issue_category": "Network & Connectivity",
        "subcategory": "No Signal / Complete Outage",
        "sentiment": "Strongly Negative",
        "urgency": "High",
        "priority": "P1",
        "department": "Network Operations & Engineering",
        "supporting_departments": [],
        "extracted_entities": {"service": "Fiber 1000", "outage_duration_hours": 48},
        "escalation_required": False,
        "escalation_reason": None,
        "escalation_level": None,
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_recommended": True,
        "resolution_steps": ["Dispatch technician", "Apply standard outage credit"],
        "professional_response": "We apologize for the 48-hour outage. A credit will be applied to your account.",
        "policy_id": "POL-001",
        "source_references": ["KB-CHUNK-01"],
        "complaint_summary": "Customer experienced 48h fiber outage."
    }


@pytest.fixture
def base_complaint():
    return {
        "id": 9001,
        "complaint_number": "CMP-9001",
        "title": "Fiber Outage",
        "description": "Fiber internet down for 48 hours in neighborhood",
        "category": "Network & Connectivity",
        "sub_category": "No Signal / Complete Outage",
        "requested_credit": 50.0,
        "escalation_required": False,
        "status": "Submitted",
        "pipeline1_status": "completed",
        "genai_analysis_result": {}
    }


@pytest.fixture
def sample_kb_docs():
    return [
        {
            "document_id": "POL-001",
            "title": "Outage & Credit Policy",
            "status": "Active",
            "category": "Network Service",
            "sections": ["Section 4.1 Credit Limits"]
        },
        {
            "document_id": "POL-OLD-99",
            "title": "Legacy Billing Rules",
            "status": "Superseded",
            "category": "Billing",
            "sections": ["Section 1"]
        }
    ]


# ── 1. UNIT TESTS: 12 INDEPENDENT VALIDATORS (24+ TESTS) ─────────────────────

def test_validate_category_pass(valid_genai_result):
    outcome = validate_category(valid_genai_result)
    assert outcome.passed is True


def test_validate_category_fail(valid_genai_result):
    mock_engine = MagicMock()
    mock_rule = MagicMock()
    mock_rule.rule_id = "RULE-001"
    mock_rule.category = "Network & Connectivity"
    mock_rule.subcategory = "No Signal / Complete Outage"
    mock_engine.match.return_value = mock_rule

    genai_fail = dict(valid_genai_result)
    genai_fail["issue_category"] = "Billing & Payments"
    genai_fail["subcategory"] = "Incorrect Charge on Invoice"
    outcome = validate_category(genai_fail, rule_matrix_engine=mock_engine)
    assert outcome.passed is False


def test_validate_department_pass(valid_genai_result):
    outcome = validate_department_routing(valid_genai_result)
    assert outcome.passed is True


def test_validate_department_fail(valid_genai_result):
    mock_engine = MagicMock()
    mock_rule = MagicMock()
    mock_rule.rule_id = "RULE-001"
    mock_rule.department = "Network Operations & Engineering"
    mock_engine.match.return_value = mock_rule

    genai_fail = dict(valid_genai_result)
    genai_fail["department"] = "Account Management"
    outcome = validate_department_routing(genai_fail, rule_matrix_engine=mock_engine)
    assert outcome.passed is False


def test_validate_urgency_pass(valid_genai_result):
    cmp = {"category": "Network & Connectivity", "description": "Intermittent fee dispute"}
    genai_result = dict(valid_genai_result)
    genai_result["urgency"] = "High"
    outcome = validate_urgency(genai_result, complaint=cmp)
    assert outcome.passed is True


def test_validate_urgency_objective_override_fail(valid_genai_result):
    cmp = {"category": "Network & Connectivity", "description": "Exposed live fiber cable poses a fire and safety hazard"}
    genai_result = dict(valid_genai_result)
    genai_result["urgency"] = "Low"
    outcome = validate_urgency(genai_result, complaint=cmp)
    assert outcome.passed is False
    assert outcome.expected_value == "Critical"


def test_validate_escalation_pass(valid_genai_result):
    cmp = {"category": "Network & Connectivity", "description": "Routine connection inquiry"}
    outcome = validate_escalation(valid_genai_result, complaint=cmp)
    assert outcome.passed is True


def test_validate_escalation_trap_fail(valid_genai_result):
    cmp = {"category": "Billing & Payments", "description": "I am reporting this unbilled charge to the FCC and hiring an attorney"}
    genai_result = dict(valid_genai_result)
    genai_result["escalation_required"] = False
    outcome = validate_escalation(genai_result, complaint=cmp)
    assert outcome.passed is False
    assert outcome.expected_value is True


def test_validate_policy_applicability_active_pass(valid_genai_result, sample_kb_docs):
    outcome = validate_policy_applicability(valid_genai_result, sample_kb_docs)
    assert outcome.passed is True


def test_validate_policy_applicability_superseded_fail(valid_genai_result, sample_kb_docs):
    genai_result = dict(valid_genai_result)
    genai_result["policy_id"] = "POL-OLD-99"
    outcome = validate_policy_applicability(genai_result, sample_kb_docs)
    assert outcome.passed is False
    assert "Superseded" in outcome.explanation


def test_validate_resolution_steps_pass(valid_genai_result):
    outcome = validate_resolution_steps(valid_genai_result)
    assert outcome.passed is True


def test_validate_resolution_steps_prohibited_fail(valid_genai_result):
    mock_engine = MagicMock()
    mock_rule = MagicMock()
    mock_rule.rule_id = "RULE-MOCK"
    mock_rule.required_actions = []
    mock_rule.prohibited_actions = ["cash refund"]
    mock_engine.match.return_value = mock_rule

    genai_result = dict(valid_genai_result)
    genai_result["resolution_steps"] = ["Issue cash refund to customer immediately"]
    outcome = validate_resolution_steps(genai_result, rule_matrix_engine=mock_engine)
    assert outcome.passed is False
    assert "prohibited" in outcome.explanation.lower()


def test_validate_refund_eligibility_pass(valid_genai_result):
    cmp = {"requested_credit": 50.0}
    outcome = validate_refund_eligibility(valid_genai_result, complaint=cmp)
    assert outcome.passed is True


def test_validate_refund_eligibility_fail(valid_genai_result):
    mock_engine = MagicMock()
    mock_rule = MagicMock()
    mock_rule.rule_id = "RULE-PROHIBIT"
    mock_rule.prohibited_actions = ["refund"]
    mock_engine.match.return_value = mock_rule

    genai_result = dict(valid_genai_result)
    genai_result["refund_eligible"] = True
    outcome = validate_refund_eligibility(genai_result, rule_matrix_engine=mock_engine)
    assert outcome.passed is False
    assert outcome.expected_value is False


def test_validate_replacement_eligibility_pass(valid_genai_result):
    genai_result = dict(valid_genai_result)
    genai_result["issue_category"] = "Device & Equipment"
    genai_result["replacement_eligible"] = True
    outcome = validate_replacement_eligibility(genai_result)
    assert outcome.passed is True


def test_validate_replacement_eligibility_fail(valid_genai_result):
    genai_result = dict(valid_genai_result)
    genai_result["issue_category"] = "Billing & Payments"
    genai_result["replacement_eligible"] = True
    outcome = validate_replacement_eligibility(genai_result)
    assert outcome.passed is False


def test_validate_compensation_pass(valid_genai_result):
    cmp = {"requested_credit": 100.0}
    outcome = validate_compensation(valid_genai_result, complaint=cmp)
    assert outcome.passed is True


def test_validate_compensation_fail(valid_genai_result):
    mock_engine = MagicMock()
    mock_rule = MagicMock()
    mock_rule.rule_id = "RULE-NO-GOODWILL"
    mock_rule.prohibited_actions = ["goodwill credit"]
    mock_engine.match.return_value = mock_rule

    genai_result = dict(valid_genai_result)
    genai_result["compensation_recommended"] = True
    outcome = validate_compensation(genai_result, rule_matrix_engine=mock_engine, complaint={"requested_credit": 50.0})
    assert outcome.passed is False


def test_detect_unsupported_promises_clean(valid_genai_result):
    flags = detect_unsupported_promises(valid_genai_result)
    assert len(flags) == 0


def test_detect_unsupported_promises_flagged(valid_genai_result):
    genai_result = dict(valid_genai_result)
    genai_result["professional_response"] = "We guarantee a full refund immediately to your bank account."
    flags = detect_unsupported_promises(genai_result)
    assert len(flags) > 0


def test_detect_hallucinated_claims_clean(valid_genai_result, base_complaint):
    flags = detect_hallucinated_claims(valid_genai_result, complaint=base_complaint, kb_chunks=[])
    assert len(flags) == 0


def test_detect_hallucinated_claims_flagged(valid_genai_result, base_complaint):
    genai_result = dict(valid_genai_result)
    genai_result["professional_response"] = "We sent your refund of $9999 to tracking number 1Z9999999999999999."
    flags = detect_hallucinated_claims(genai_result, complaint=base_complaint, kb_chunks=[])
    assert len(flags) > 0


def test_detect_contradictory_instructions_clean(sample_kb_docs):
    flags = detect_contradictory_instructions(kb_documents=[sample_kb_docs[0]])
    assert len(flags) == 0


def test_detect_contradictory_instructions_flagged(sample_kb_docs):
    docs = list(sample_kb_docs)
    docs.append({
        "document_id": "POL-DRAFT-02",
        "title": "Draft Network Rules",
        "status": "Draft",
        "category": "Network Service"
    })
    flags = detect_contradictory_instructions(kb_documents=docs)
    assert len(flags) > 0


# ── 2. ACCEPTANCE CRITERIA 2: E2E ESCALATION TRAP TEST ───────────────────────

def test_e2e_escalation_trap_python_overrides_genai(valid_genai_result, base_complaint, sample_kb_docs):
    cmp = dict(base_complaint)
    cmp["description"] = "Unresolved billing fraud, I will take legal action and contact the FCC!"

    genai = dict(valid_genai_result)
    genai["escalation_required"] = False

    report = compare_and_verify(genai, cmp, kb_documents=sample_kb_docs)

    assert report["final_status"] == "Manual Review Required"
    assert report["overwritten_fields"].get("escalation_required") is True
    assert cmp["escalation_required"] is True


# ── 3. ACCEPTANCE CRITERIA 3: SUPERSEDED POLICY TEST ────────────────────────

def test_e2e_superseded_policy_routes_to_manual_review(valid_genai_result, base_complaint, sample_kb_docs):
    genai = dict(valid_genai_result)
    genai["policy_id"] = "POL-OLD-99"

    report = compare_and_verify(genai, base_complaint, kb_documents=sample_kb_docs)

    assert report["final_status"] == "Manual Review Required"
    assert report["field_comparisons"]["policy"]["passed"] is False
    assert any("Superseded" in m for m in report["mismatches"])


# ── 4. ACCEPTANCE CRITERIA 4: UNSUPPORTED PROMISES TEST ──────────────────────

def test_e2e_unsupported_promises_routes_to_manual_review(valid_genai_result, base_complaint, sample_kb_docs):
    genai = dict(valid_genai_result)
    genai["professional_response"] = "We guarantee a full refund immediately to your bank account."

    report = compare_and_verify(genai, base_complaint, kb_documents=sample_kb_docs)

    assert report["final_status"] == "Manual Review Required"
    assert len(report["unsupported_promises"]) > 0


# ── 5. ACCEPTANCE CRITERIA 5: SCHEMA PRE-CHECK TEST ─────────────────────────

def test_e2e_schema_pre_check_failure_skips_part_a(base_complaint):
    bad_genai = {
        "complaint_id": "9001",
        "primary_issue": "Billing issue",
        "issue_category": "Billing & Payments",
        "subcategory": "Incorrect Charge on Invoice",
        "sentiment": "Strongly Negative",
        "urgency": "SuperUrgent",  # INVALID ENUM VALUE
        "priority": "P1",
        "department": "Billing & Revenue Assurance",
        "professional_response": "We will review your fee.",
        "complaint_summary": "Fee dispute"
    }

    with patch("backend.comparison_engine.engine.validate_category") as mock_val_cat:
        report = compare_and_verify(bad_genai, base_complaint)

        assert report["pipeline2_status"] == "schema_invalid"
        assert report["final_status"] == "Manual Review Required"
        assert base_complaint["pipeline2_status"] == "schema_invalid"
        mock_val_cat.assert_not_called()
