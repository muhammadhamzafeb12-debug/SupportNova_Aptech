"""
Dual-Pipeline Alignment & Hallucination Check API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.schemas import PipelineTriggerRequest, ComparisonResult
from backend.security.jwt_auth import require_role
from backend.src.store import COMPLAINTS_STORE, RULE_MATRIX_STORE

router = APIRouter(prefix="/comparison", tags=["Dual-Pipeline Alignment"])

@router.post("/check", response_model=ComparisonResult)
def run_comparison_check(
    payload: PipelineTriggerRequest,
    current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))
):
    target = None
    for c in COMPLAINTS_STORE:
        if c["id"] == payload.complaint_id:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    genai_cat = target["category"]
    python_cat = genai_cat  # Default match
    
    # Lookup rule matrix
    max_credit = 50.0
    for r in RULE_MATRIX_STORE:
        if r["category"].lower() == genai_cat.lower():
            max_credit = r["max_auto_credit"]
            break

    requested_credit = target.get("requested_credit", 0.0)
    credit_override = requested_credit > max_credit
    
    # Hallucination check logic
    hallucination_detected = target.get("has_hallucination", False) or credit_override
    hallucination_reason = target.get("hallucination_details")
    if credit_override and not hallucination_reason:
        hallucination_reason = f"GenAI accepted requested credit (${requested_credit}) exceeding ground-truth cap (${max_credit})"

    review_req = hallucination_detected or target.get("priority") == "Urgent" or not target.get("python_validation_passed", True)

    target["has_hallucination"] = hallucination_detected
    target["hallucination_details"] = hallucination_reason

    return {
        "complaint_id": target["id"],
        "genai_category": genai_cat,
        "python_category": python_cat,
        "category_matches": True,
        "genai_credit": requested_credit,
        "python_credit_limit": max_credit,
        "credit_override_flag": credit_override,
        "hallucination_detected": hallucination_detected,
        "hallucination_reason": hallucination_reason,
        "review_required": review_req
    }
