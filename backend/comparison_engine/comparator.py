"""
Comparison Engine for SupportNova (GenAI Pipeline 1 vs Independent Python Pipeline 2).
Compares GenAI predictions against deterministic Python ground truth across 7 compliance scorecards.
"""

from typing import List, Dict, Any, Tuple
from backend.schemas.schemas import GenAIResponseSchema, PythonValidationSchema, MismatchDetail

def compare_genai_vs_python(
    genai_output: GenAIResponseSchema,
    python_output: PythonValidationSchema
) -> Tuple[str, float, float, float, float, float, float, float, float, List[MismatchDetail]]:
    """
    Compares GenAI Pipeline 1 output against Python Ground-Truth Pipeline 2 output.
    Returns (overall_status, schema_score, policy_score, routing_score, urgency_score, escalation_score, resolution_score, traceability_score, overall_score, mismatches).
    """
    mismatches: List[MismatchDetail] = []
    
    # 1. Category check
    if genai_output.category.lower() != python_output.verified_category.lower():
        mismatches.append(MismatchDetail(
            field="category",
            genai_val=genai_output.category,
            expected_val=python_output.verified_category,
            reason=f"GenAI predicted category '{genai_output.category}' but Python rule matrix mandates '{python_output.verified_category}'.",
            severity="HIGH" if python_output.verified_category in ["Safety", "Privacy"] else "MEDIUM"
        ))
        
    # 2. Subcategory check
    if genai_output.subcategory.lower() != python_output.verified_subcategory.lower():
        mismatches.append(MismatchDetail(
            field="subcategory",
            genai_val=genai_output.subcategory,
            expected_val=python_output.verified_subcategory,
            reason=f"GenAI subcategory '{genai_output.subcategory}' differs from ground truth '{python_output.verified_subcategory}'.",
            severity="LOW"
        ))

    # 3. Department Routing check
    if genai_output.department.lower() != python_output.verified_department.lower():
        mismatches.append(MismatchDetail(
            field="department",
            genai_val=genai_output.department,
            expected_val=python_output.verified_department,
            reason=f"GenAI routed complaint to '{genai_output.department}', but deterministic routing mandates '{python_output.verified_department}'.",
            severity="HIGH"
        ))

    # 4. Urgency check
    if genai_output.urgency.lower() != python_output.verified_urgency.lower():
        mismatches.append(MismatchDetail(
            field="urgency",
            genai_val=genai_output.urgency,
            expected_val=python_output.verified_urgency,
            reason=f"GenAI assigned urgency '{genai_output.urgency}' while Python business rules mandate '{python_output.verified_urgency}'.",
            severity="CRITICAL" if python_output.verified_urgency == "Critical" else "MEDIUM"
        ))

    # 5. Priority check
    if genai_output.priority.lower() != python_output.verified_priority.lower():
        mismatches.append(MismatchDetail(
            field="priority",
            genai_val=genai_output.priority,
            expected_val=python_output.verified_priority,
            reason=f"GenAI priority '{genai_output.priority}' contradicts Python rule priority '{python_output.verified_priority}'.",
            severity="MEDIUM"
        ))

    # 6. Escalation check
    if genai_output.escalation_required != python_output.verified_escalation_required:
        mismatches.append(MismatchDetail(
            field="escalation_required",
            genai_val=genai_output.escalation_required,
            expected_val=python_output.verified_escalation_required,
            reason=f"GenAI escalation ({genai_output.escalation_required}) contradicts mandatory Python ground truth ({python_output.verified_escalation_required}). Reason: {python_output.verified_escalation_reason}",
            severity="CRITICAL"
        ))

    # 7. Refund Eligibility Mismatch
    # E.g. GenAI promised refund in response/steps but Python eligibility rules say False
    genai_claims_refund = "refund" in (genai_output.customer_response or "").lower() or any("refund" in s.lower() for s in genai_output.resolution_steps)
    if genai_claims_refund and not python_output.verified_refund_eligible:
        mismatches.append(MismatchDetail(
            field="refund_eligibility",
            genai_val=True,
            expected_val=False,
            reason="GenAI promised/recommended refund, but complaint is not eligible under Python business rules.",
            severity="HIGH"
        ))

    # 8. Replacement Eligibility Mismatch
    genai_claims_replacement = "replacement" in (genai_output.customer_response or "").lower() or any("replace" in s.lower() for s in genai_output.resolution_steps)
    if genai_claims_replacement and not python_output.verified_replacement_eligible:
        mismatches.append(MismatchDetail(
            field="replacement_eligibility",
            genai_val=True,
            expected_val=False,
            reason="GenAI recommended product replacement, but item is ineligible (e.g. warranty expired or non-defective).",
            severity="HIGH"
        ))

    # 9. Compensation Eligibility Mismatch
    genai_claims_comp = "compensation" in (genai_output.customer_response or "").lower() or "gift card" in (genai_output.customer_response or "").lower()
    if genai_claims_comp and not python_output.verified_compensation_eligible:
        mismatches.append(MismatchDetail(
            field="compensation_eligibility",
            genai_val=True,
            expected_val=False,
            reason="GenAI promised compensation, but customer is ineligible under store credit policy POL-016.",
            severity="HIGH"
        ))

    # 10. Unsupported Claims / Hallucinations
    for claim in python_output.unsupported_claims:
        mismatches.append(MismatchDetail(
            field="unsupported_claim",
            genai_val="Prohibited claim in customer response",
            expected_val="Strict policy grounding without unapproved guarantees",
            reason=claim,
            severity="CRITICAL"
        ))

    # 11. Missing Mandatory Actions
    for missing in python_output.missing_actions:
        mismatches.append(MismatchDetail(
            field="resolution_steps",
            genai_val="Incomplete action list",
            expected_val=missing,
            reason=missing,
            severity="LOW"
        ))

    # 12. Policy Grounding
    if not python_output.policy_grounding_valid:
        mismatches.append(MismatchDetail(
            field="policy_references",
            genai_val=[ref.get("doc_id") for ref in genai_output.policy_references],
            expected_val=python_output.verified_policy_id,
            reason="GenAI cited unapproved, outdated, or hallucinated policy documentation.",
            severity="HIGH"
        ))

    # Calculate compliance scores based on empirical validation results (SRS requirement #21)
    schema_score = 100.0  # Already validated via Pydantic
    
    routing_score = 100.0 if not any(m.field == "department" for m in mismatches) else 0.0
    urgency_score = 100.0 if not any(m.field in ["urgency", "priority"] for m in mismatches) else 40.0
    escalation_score = 100.0 if not any(m.field == "escalation_required" for m in mismatches) else 0.0
    policy_score = 100.0 if python_output.policy_grounding_valid and not any(m.field == "policy_references" for m in mismatches) else 30.0
    resolution_score = max(0.0, 100.0 - (len(python_output.missing_actions) * 20.0) - (sum(1 for m in mismatches if "eligibility" in m.field) * 30.0))
    traceability_score = 100.0 if len(genai_output.policy_references) > 0 else 50.0

    weights = {
        "schema": 0.10,
        "policy": 0.20,
        "routing": 0.15,
        "urgency": 0.15,
        "escalation": 0.20,
        "resolution": 0.10,
        "traceability": 0.10
    }

    overall_score = (
        schema_score * weights["schema"] +
        policy_score * weights["policy"] +
        routing_score * weights["routing"] +
        urgency_score * weights["urgency"] +
        escalation_score * weights["escalation"] +
        resolution_score * weights["resolution"] +
        traceability_score * weights["traceability"]
    )
    overall_score = round(overall_score, 2)

    # Determine overall status
    critical_mismatches = [m for m in mismatches if m.severity == "CRITICAL"]
    high_mismatches = [m for m in mismatches if m.severity == "HIGH"]

    if critical_mismatches or overall_score < 70.0:
        overall_status = "REVIEW REQUIRED"
    elif high_mismatches or overall_score < 85.0:
        overall_status = "MISMATCH"
    elif mismatches:
        overall_status = "WARNING"
    else:
        overall_status = "MATCH"

    return (
        overall_status,
        schema_score,
        policy_score,
        routing_score,
        urgency_score,
        escalation_score,
        resolution_score,
        traceability_score,
        overall_score,
        mismatches
    )
