"""
Pipeline 2 Comparison Engine for SupportNova.
Executes Part B schema pre-check, Part A independent validators, computes weighted verification score,
enforces critical precedence overrides (escalation, policy), and determines final status ('Verified' vs 'Manual Review Required').
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.python_validation.schema_check import pre_check_schema
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
from backend.complaint_rules.engine import RuleMatrixEngine
from backend.src.store import (
    COMPLAINTS_STORE,
    KNOWLEDGE_BASE_STORE,
    VERIFICATION_REPORTS_STORE
)

logger = logging.getLogger(__name__)


def compare_and_verify(
    genai_result: Optional[Dict[str, Any]],
    complaint: Dict[str, Any],
    kb_documents: Optional[List[Dict[str, Any]]] = None,
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    db_session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes complete Pipeline 2 Ground-Truth Verification & Comparison Engine.
    
    CRITICAL PRECEDENCE RULE:
    On compliance-critical fields (escalation_required, policy_id, prohibited_actions),
    Python's rule-matrix validation result is the FINAL answer used in the actual complaint record —
    GenAI's value on these fields is advisory-only and gets overwritten if they disagree.
    
    Category/department/urgency mismatches route to Manual Review for human judgment.
    """
    cid = str(complaint.get("complaint_number") or complaint.get("id"))
    docs = kb_documents if kb_documents is not None else KNOWLEDGE_BASE_STORE
    engine = rule_matrix_engine or RuleMatrixEngine()

    # ── PART B: Schema Pre-Check ──────────────────────────────────────────────
    if not genai_result:
        report = {
            "complaint_id": cid,
            "verification_score": 0.0,
            "final_status": "Manual Review Required",
            "pipeline2_status": "schema_invalid",
            "failure_reason": "GenAI result is missing or null.",
            "field_comparisons": {},
            "mismatches": ["GenAI analysis missing."],
            "unsupported_promises": [],
            "hallucinated_claims": [],
            "contradictions": [],
            "overwritten_fields": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        complaint["pipeline2_status"] = "schema_invalid"
        complaint["pipeline2_failure_reason"] = "GenAI analysis missing."
        complaint["python_verification_report"] = report
        VERIFICATION_REPORTS_STORE.append(report)
        return report

    schema_ok, schema_errors = pre_check_schema(genai_result)
    if not schema_ok:
        report = {
            "complaint_id": cid,
            "verification_score": 0.0,
            "final_status": "Manual Review Required",
            "pipeline2_status": "schema_invalid",
            "failure_reason": f"Schema Pre-Check Failed: {'; '.join(schema_errors)}",
            "field_comparisons": {},
            "mismatches": schema_errors,
            "unsupported_promises": [],
            "hallucinated_claims": [],
            "contradictions": [],
            "overwritten_fields": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        complaint["pipeline2_status"] = "schema_invalid"
        complaint["pipeline2_failure_reason"] = report["failure_reason"]
        complaint["python_verification_report"] = report
        VERIFICATION_REPORTS_STORE.append(report)
        return report

    # ── PART A: Execute 12 Independent Validators ─────────────────────────────
    val_cat = validate_category(genai_result, engine, complaint)
    val_dept = validate_department_routing(genai_result, engine, complaint)
    val_urg = validate_urgency(genai_result, engine, complaint)
    val_esc = validate_escalation(genai_result, engine, complaint)
    val_pol = validate_policy_applicability(genai_result, docs)
    val_steps = validate_resolution_steps(genai_result, engine, complaint)
    val_ref = validate_refund_eligibility(genai_result, engine, complaint=complaint)
    val_rep = validate_replacement_eligibility(genai_result, engine, complaint=complaint)
    val_comp = validate_compensation(genai_result, engine, complaint=complaint)

    # Matched rule for promise check
    matched_rule = engine.match({
        "category": complaint.get("category", ""),
        "subcategory": complaint.get("sub_category") or complaint.get("subcategory", ""),
        "description": complaint.get("description", "")
    })

    unsupported_promises = detect_unsupported_promises(genai_result, matched_rule)
    hallucinated_claims = detect_hallucinated_claims(genai_result, complaint, [])
    contradictions = detect_contradictory_instructions([], docs)

    # ── WEIGHTED VERIFICATION SCORE COMPUTATION (0 - 100) ────────────────────
    """
    Weighting Formula:
    - Escalation Correctness: 25 points (compliance critical)
    - Policy Applicability: 20 points (active policy reference)
    - Resolution Required/Prohibited Actions: 15 points (procedural accuracy)
    - Department Routing: 10 points (triage routing)
    - Urgency Alignment: 10 points (SLA classification)
    - Refund/Compensation Eligibility: 10 points (financial threshold)
    - Category Alignment: 10 points (taxonomy classification)
    - Deductions: -10 points per unsupported promise or hallucinated claim flag
    """
    score = 0.0
    score += 25.0 if val_esc.passed else 0.0
    score += 20.0 if val_pol.passed else 0.0
    score += 15.0 if val_steps.passed else 0.0
    score += 10.0 if val_dept.passed else 0.0
    score += 10.0 if val_urg.passed else 0.0
    score += 10.0 if (val_ref.passed and val_comp.passed) else 5.0
    score += 10.0 if val_cat.passed else 0.0

    # Penalties for flags
    penalties = (len(unsupported_promises) + len(hallucinated_claims)) * 10.0
    final_score = max(0.0, round(score - penalties, 1))

    # Collect Mismatches
    mismatches = []
    if not val_cat.passed:
        mismatches.append(f"Category mismatch: GenAI={val_cat.actual_value}, Expected={val_cat.expected_value}")
    if not val_dept.passed:
        mismatches.append(f"Department mismatch: GenAI='{val_dept.actual_value}', Expected='{val_dept.expected_value}'")
    if not val_urg.passed:
        mismatches.append(f"Urgency mismatch: GenAI='{val_urg.actual_value}', Objective Expected='{val_urg.expected_value}'")
    if not val_esc.passed:
        mismatches.append(f"Escalation mismatch: GenAI={val_esc.actual_value}, Python Ground-Truth Enforces={val_esc.expected_value}")
    if not val_pol.passed:
        mismatches.append(f"Policy applicability failure: {val_pol.explanation}")
    if not val_steps.passed:
        mismatches.append(f"Resolution steps failure: {val_steps.explanation}")

    # Determine Final Status
    has_compliance_issue = (not val_esc.passed) or (not val_pol.passed) or (not val_steps.passed)
    has_flags = len(unsupported_promises) > 0 or len(hallucinated_claims) > 0

    if final_score >= 85.0 and not has_compliance_issue and not has_flags and len(mismatches) == 0:
        final_status = "Verified"
    else:
        final_status = "Manual Review Required"

    # ── CRITICAL PRECEDENCE OVERWRITES ON COMPLAINT RECORD ─────────────────────
    overwritten_fields = {}
    if val_esc.expected_value is True and not genai_result.get("escalation_required"):
        overwritten_fields["escalation_required"] = True
        complaint["escalation_required"] = True
        complaint["escalation_level"] = (matched_rule.escalation_level if matched_rule else "Tier 1") or "Tier 1"
        logger.info("OVERRODE GenAI escalation_required=False -> True based on objective rule precedence.")

    if val_pol.passed and matched_rule and matched_rule.policy_id:
        overwritten_fields["policy_id"] = matched_rule.policy_id
        genai_result["policy_id"] = matched_rule.policy_id

    # Update Complaint status
    complaint["pipeline2_status"] = "completed"
    complaint["pipeline2_failure_reason"] = None
    if final_status == "Manual Review Required":
        complaint["status"] = "Review Required"

    field_comparisons = {
        "category": val_cat.to_dict(),
        "department": val_dept.to_dict(),
        "urgency": val_urg.to_dict(),
        "escalation": val_esc.to_dict(),
        "policy": val_pol.to_dict(),
        "resolution_steps": val_steps.to_dict(),
        "refund_eligibility": val_ref.to_dict(),
        "replacement_eligibility": val_rep.to_dict(),
        "compensation": val_comp.to_dict()
    }

    report = {
        "complaint_id": cid,
        "verification_score": final_score,
        "final_status": final_status,
        "pipeline2_status": "completed",
        "failure_reason": None,
        "field_comparisons": field_comparisons,
        "mismatches": mismatches,
        "unsupported_promises": unsupported_promises,
        "hallucinated_claims": hallucinated_claims,
        "contradictions": contradictions,
        "overwritten_fields": overwritten_fields,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    complaint["python_verification_report"] = report
    VERIFICATION_REPORTS_STORE.append(report)

    return report
