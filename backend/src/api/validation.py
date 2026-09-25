"""
Python Ground-Truth Validation API Router
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.schemas import PipelineTriggerRequest, ValidationResult
from backend.security.jwt_auth import require_role
from backend.src.store import COMPLAINTS_STORE, RULE_MATRIX_STORE

router = APIRouter(prefix="/validation", tags=["Python Validation"])

@router.post("/run", response_model=ValidationResult)
def run_python_validation(
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

    flags: List[str] = []
    category = target["category"]
    
    # Lookup rule matrix
    rule = None
    for r in RULE_MATRIX_STORE:
        if r["category"].lower() == category.lower():
            rule = r
            break

    suggested_dept = rule["primary_department"] if rule else "General Support"
    max_credit = rule["max_auto_credit"] if rule else 50.0
    regulatory = rule["regulatory_trigger"] if rule else False

    # Perform ground truth validation checks
    req_credit = target.get("requested_credit", 0.0)
    if req_credit > max_credit:
        flags.append(f"Requested credit (${req_credit}) exceeds rule ceiling (${max_credit})")

    desc_lower = target["description"].lower()
    if "fcc" in desc_lower or "legal" in desc_lower or "attorney" in desc_lower:
        regulatory = True
        flags.append("Regulatory threat detected (FCC/Legal keywords present)")

    if regulatory:
        flags.append("Escalation triggered: Requires Senior Manager or Legal approval")

    passed = len(flags) == 0
    target["python_validation_passed"] = passed
    target["python_validation_flags"] = flags

    return {
        "complaint_id": target["id"],
        "passed": passed,
        "flags": flags,
        "suggested_department": suggested_dept,
        "recommended_credit": min(req_credit, max_credit),
        "regulatory_warning": regulatory
    }
