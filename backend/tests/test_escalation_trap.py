"""
SupportNova Pipeline 2 — Dedicated Escalation Trap Adversarial Test.

SRS Requirement:
"A complaint may contain an escalation condition that is easily overlooked by GenAI.
The Python pipeline must independently enforce the escalation rule."

Demonstrates the security-critical precedence rule where pure deterministic Python business rules
override GenAI advisory outputs when an escalation condition is missed by the GenAI model.
"""
import pytest
import logging
from unittest.mock import MagicMock

from backend.python_validation.validators import validate_escalation
from backend.comparison_engine.engine import compare_and_verify
from backend.complaint_rules.engine import RuleMatrixEngine, MatchedRule

logger = logging.getLogger(__name__)


def test_escalation_trap_adversarial_precedence():
    """
    Escalation Trap Test Scenario:
    1. A complaint involves an unauthorized account security breach ("SIM swap" / "account takeover").
    2. The Complaint Resolution Rule Matrix matched rule enforces escalation_required=True.
    3. GenAI incorrectly predicts escalation_required=False (missing the critical trigger).
    4. Python Pipeline 2 detects the mismatch, overrides GenAI on the complaint record,
       and forces the complaint status to 'Manual Review Required'.
    """
    # Step 1: Mock/Create Rule Matrix Engine with an active escalation rule
    mock_engine = MagicMock(spec=RuleMatrixEngine)
    security_rule = MatchedRule(
        rule_id="RULE-SEC-001",
        category="Account Security & Fraud",
        subcategory="Unauthorized SIM Swap / Port-Out",
        department="Account Security & Fraud Prevention",
        supporting_departments=[],
        urgency="Critical",
        priority="P0",
        policy_id="POL-SEC-2026",
        escalation_required=True,
        escalation_level="Tier 2 Security Lead",
        required_actions=["Lock account", "Initiate identity verification"],
        prohibited_actions=["Unlock without ID verification"],
        follow_up_required=True,
        conditions={"keywords": ["sim swap", "unauthorized", "takeover"]}
    )
    mock_engine.match.return_value = security_rule

    # Step 2: Craft complaint matching security breach conditions
    complaint_record = {
        "id": 9999,
        "complaint_number": "CMP-TRAP-9999",
        "title": "My SIM card was swapped without authorization",
        "description": "I suddenly lost signal and received an email saying my SIM was swapped. Someone is trying an account takeover!",
        "category": "Account Security & Fraud",
        "sub_category": "Unauthorized SIM Swap / Port-Out",
        "requested_credit": 0.0,
        "escalation_required": False,  # Initial raw state
        "status": "Submitted",
        "pipeline1_status": "completed",
        "genai_analysis_result": {}
    }

    # Step 3: Mock Pipeline 1 GenAI response — simulating GenAI MISSING the escalation trigger
    mocked_genai_result = {
        "complaint_id": "9999",
        "primary_issue": "SIM card swap reported",
        "secondary_issues": [],
        "issue_category": "Account Security & Fraud",
        "subcategory": "Unauthorized SIM Swap / Port-Out",
        "sentiment": "Strongly Negative",
        "urgency": "Critical",
        "priority": "P0",
        "department": "Account Security & Fraud Prevention",
        "supporting_departments": [],
        "extracted_entities": {"account_number": "ACC-88219"},
        "escalation_required": False,  # REALISTIC FAILURE MODE: GenAI missed escalation!
        "escalation_reason": None,
        "escalation_level": None,
        "refund_eligible": False,
        "replacement_eligible": True,
        "compensation_recommended": False,
        "resolution_steps": ["Verify customer identity"],
        "professional_response": "We have received your request regarding your SIM card change.",
        "policy_id": "POL-SEC-2026",
        "source_references": ["KB-SEC-01"],
        "complaint_summary": "Customer reported SIM swap."
    }

    # Step 4: Run Pipeline 2 validate_escalation() function directly
    val_outcome = validate_escalation(
        genai_result=mocked_genai_result,
        rule_matrix_engine=mock_engine,
        complaint=complaint_record
    )

    # Assert 5a: validate_escalation() returns passed=False with actual_value=False, expected_value=True
    assert val_outcome.passed is False, \
        f"FAILED 5a: validate_escalation() should fail when GenAI misses escalation. Explanation: {val_outcome.explanation}"
    assert val_outcome.actual_value is False, \
        f"FAILED 5a: actual_value should be False (what GenAI outputted), got {val_outcome.actual_value}"
    assert val_outcome.expected_value is True, \
        f"FAILED 5a: expected_value should be True (what Python Rule Matrix enforces), got {val_outcome.expected_value}"
    assert val_outcome.rule_id_used == "RULE-SEC-001"

    print("\n✅ Assertion 5a PASSED: validate_escalation() correctly identified GenAI escalation omission.")

    # Step 4b: Execute Comparison Engine compare_and_verify()
    verification_report = compare_and_verify(
        genai_result=mocked_genai_result,
        complaint=complaint_record,
        kb_documents=[{
            "document_id": "POL-SEC-2026",
            "title": "Security Incident Policy",
            "status": "Active",
            "category": "Account Security & Fraud"
        }],
        rule_matrix_engine=mock_engine
    )

    # Assert 5b: The final VerificationReport shows escalation_required=True in Python-verified column
    esc_field_comp = verification_report["field_comparisons"]["escalation"]
    assert esc_field_comp["expected_value"] is True, \
        f"FAILED 5b: Python-verified column in report must show expected_value=True, got {esc_field_comp['expected_value']}"
    assert esc_field_comp["actual_value"] is False, \
        f"FAILED 5b: Report must capture actual_value=False from GenAI output, got {esc_field_comp['actual_value']}"

    print("✅ Assertion 5b PASSED: VerificationReport records Python-verified escalation_required=True vs GenAI=False.")

    # Assert 5c: Saved complaint record reflects escalation_required=True as authoritative value
    assert complaint_record["escalation_required"] is True, \
        f"FAILED 5c: Complaint record escalation_required should be overridden to True, got {complaint_record['escalation_required']}"
    assert verification_report["overwritten_fields"].get("escalation_required") is True, \
        f"FAILED 5c: overwritten_fields in verification report must record escalation_required=True override"
    assert complaint_record["escalation_level"] == "Tier 2 Security Lead", \
        f"FAILED 5c: Complaint record escalation_level should be updated to 'Tier 2 Security Lead'"

    print("✅ Assertion 5c PASSED: Complaint record authoritative value overrode GenAI to escalation_required=True.")

    # Assert 5d: final_status is "Manual Review Required"
    assert verification_report["final_status"] == "Manual Review Required", \
        f"FAILED 5d: Escalation mismatch must route complaint to 'Manual Review Required', got '{verification_report['final_status']}'"
    assert complaint_record["status"] == "Review Required", \
        f"FAILED 5d: Complaint status must update to 'Review Required', got '{complaint_record['status']}'"

    print("✅ Assertion 5d PASSED: Final status correctly set to 'Manual Review Required' due to compliance mismatch.")
    print("🎉 ALL ESCALATION TRAP E2E ADVERSARIAL ASSERTIONS PASSED SUCCESSFULLY!\n")
