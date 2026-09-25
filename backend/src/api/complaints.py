"""
Complaints API Router
"""
import random
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from backend.schemas.schemas import ComplaintCreate, ComplaintUpdate, ComplaintResponse
from backend.security.jwt_auth import get_current_user, require_role
from backend.src.store import COMPLAINTS_STORE, AUDIT_LOGS_STORE, RULE_MATRIX_STORE

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.get("", response_model=List[ComplaintResponse])
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    customer_email: Optional[str] = Query(None, alias="customer_email"),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    results = list(COMPLAINTS_STORE)

    # Role-based restriction: Customers can only see their own complaints
    user_role = current_user.get("role", "").lower().strip()
    if user_role == "customer":
        results = [c for c in results if c["customer_email"].lower() == current_user["username"].lower()]

    if status_filter:
        results = [c for c in results if c["status"].lower() == status_filter.lower()]
    if category_filter:
        results = [c for c in results if c["category"].lower() == category_filter.lower()]
    if customer_email:
        results = [c for c in results if c["customer_email"].lower() == customer_email.lower()]
    if search:
        s = search.lower()
        results = [
            c for c in results 
            if s in c["complaint_number"].lower() 
            or s in c["title"].lower() 
            or s in c["description"].lower() 
            or s in c["customer_name"].lower()
        ]
    return results

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreate,
    current_user: dict = Depends(get_current_user)
):
    new_id = max([c["id"] for c in COMPLAINTS_STORE] or [0]) + 1
    complaint_number = f"CMP-2026-{1000 + new_id}"
    
    # Lookup rule matrix for assigned department
    assigned_dept = "Billing & Revenue Assurance"
    for r in RULE_MATRIX_STORE:
        if r.get("category", "").lower() == payload.category.lower():
            assigned_dept = r.get("department", "Billing & Revenue Assurance")
            break

    # Simulated GenAI processing
    sentiment = max(0.05, min(0.95, round(1.0 - (len(payload.description) / 500.0), 2)))
    summary = f"Summary: {payload.title}. {payload.description[:100]}..."
    suggested_resp = f"Dear {payload.customer_name}, Thank you for contacting NexaLink Communications. We are looking into your complaint regarding {payload.category}."

    complaint_dict = {
        "id": new_id,
        "complaint_number": complaint_number,
        "customer_email": payload.customer_email,
        "customer_name": payload.customer_name,
        "account_number": payload.account_number or "",
        "title": payload.title,
        "category": payload.category,
        "sub_category": payload.sub_category or "",
        "description": payload.description,
        "status": "Submitted",
        "priority": "High" if "urgent" in payload.description.lower() or "fcc" in payload.description.lower() else "Medium",
        "assigned_department": assigned_dept,
        "assigned_agent": None,
        "sentiment_score": sentiment,
        "genai_summary": summary,
        "genai_suggested_response": suggested_resp,
        "genai_confidence": 0.89,
        "python_validation_passed": True,
        "python_validation_flags": [],
        "has_hallucination": False,
        "hallucination_details": None,
        "requested_credit": payload.requested_credit or 0.0,
        "approved_credit": 0.0,
        "resolution_notes": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    COMPLAINTS_STORE.insert(0, complaint_dict)

    AUDIT_LOGS_STORE.append({
        "id": len(AUDIT_LOGS_STORE) + 1,
        "complaint_number": complaint_number,
        "action": "Complaint Submitted",
        "performed_by": current_user["username"],
        "details": f"Created via API by {current_user['full_name']}",
        "timestamp": datetime.utcnow().isoformat()
    })

    return complaint_dict

@router.get("/{identifier}", response_model=ComplaintResponse)
def get_complaint(identifier: str, current_user: dict = Depends(get_current_user)):
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Role permission check
    user_role = current_user.get("role", "").lower().strip()
    if user_role == "customer" and target["customer_email"].lower() != current_user["username"].lower():
        raise HTTPException(status_code=403, detail="Forbidden access to this complaint")

    return target

@router.patch("/{identifier}", response_model=ComplaintResponse)
def update_complaint(
    identifier: str,
    payload: ComplaintUpdate,
    current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))
):
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if payload.status:
        target["status"] = payload.status
    if payload.priority:
        target["priority"] = payload.priority
    if payload.assigned_department:
        target["assigned_department"] = payload.assigned_department
    if payload.assigned_agent:
        target["assigned_agent"] = payload.assigned_agent
    if payload.resolution_notes is not None:
        target["resolution_notes"] = payload.resolution_notes
    if payload.approved_credit is not None:
        target["approved_credit"] = payload.approved_credit

    target["updated_at"] = datetime.utcnow().isoformat()

    AUDIT_LOGS_STORE.append({
        "id": len(AUDIT_LOGS_STORE) + 1,
        "complaint_number": target["complaint_number"],
        "action": "Complaint Updated",
        "performed_by": current_user["username"],
        "details": f"Updated status to {target['status']}, agent to {target['assigned_agent']}",
        "timestamp": datetime.utcnow().isoformat()
    })

    return target


from fastapi import BackgroundTasks
from backend.genai_pipeline.pipeline import analyze_complaint


@router.post("/{identifier}/analyze")
async def trigger_complaint_analysis(
    identifier: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))
):
    """Triggers Pipeline 1 GenAI Complaint Analysis for the given complaint."""
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    target["pipeline1_status"] = "processing"

    # Execute analysis
    result = await analyze_complaint(target)

    return {
        "complaint_id": target["id"],
        "complaint_number": target["complaint_number"],
        "pipeline1_status": target.get("pipeline1_status", "completed"),
        "failure_reason": target.get("pipeline1_failure_reason"),
        "analysis_result": result.get("analysis_result")
    }


@router.get("/{identifier}/analysis")
def get_complaint_analysis(
    identifier: str,
    current_user: dict = Depends(get_current_user)
):
    """Returns the current ComplaintAnalysisResult + pipeline1_status for that complaint."""
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {
        "complaint_id": target["id"],
        "complaint_number": target["complaint_number"],
        "pipeline1_status": target.get("pipeline1_status", "unprocessed"),
        "failure_reason": target.get("pipeline1_failure_reason"),
        "analysis_result": target.get("genai_analysis_result")
    }


@router.post("/{identifier}/validate")
def validate_complaint(
    identifier: str,
    current_user: dict = Depends(get_current_user)
):
    """Triggers Pipeline 2 Ground-Truth Validation & Comparison Engine for a complaint."""
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    genai_result = target.get("genai_analysis_result")
    from backend.comparison_engine.engine import compare_and_verify
    report = compare_and_verify(genai_result, target)
    return report


@router.get("/{identifier}/verification")
def get_complaint_verification(
    identifier: str,
    current_user: dict = Depends(get_current_user)
):
    """Returns the VerificationReport generated by Pipeline 2 for a complaint."""
    target = None
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == identifier or c["complaint_number"].lower() == identifier.lower():
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    report = target.get("python_verification_report")
    if not report:
        raise HTTPException(status_code=404, detail="Verification report not found for this complaint. Run validation first.")

    return report


