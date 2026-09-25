"""
Dashboards API Router
Provides customized operational views for Customer, Agent, Reviewer, Manager, and Admin roles.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from backend.security.jwt_auth import get_current_user, require_role
from backend.src.store import (
    COMPLAINTS_STORE,
    KNOWLEDGE_BASE_STORE,
    RULE_MATRIX_STORE,
    AUDIT_LOGS_STORE
)

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])

@router.get("/customer")
def get_customer_dashboard(current_user: dict = Depends(get_current_user)):
    user_email = current_user["username"].lower()
    my_complaints = [c for c in COMPLAINTS_STORE if c["customer_email"].lower() == user_email]
    
    total = len(my_complaints)
    resolved = len([c for c in my_complaints if c["status"] == "Resolved"])
    pending = total - resolved
    total_credits = sum([c.get("approved_credit", 0.0) for c in my_complaints])

    return {
        "user_name": current_user["full_name"],
        "metrics": {
            "total_submitted": total,
            "pending_resolution": pending,
            "resolved_complaints": resolved,
            "total_credits_approved": round(total_credits, 2)
        },
        "complaints": my_complaints
    }

@router.get("/agent")
def get_agent_dashboard(current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))):
    all_complaints = list(COMPLAINTS_STORE)
    unassigned = [c for c in all_complaints if not c.get("assigned_agent")]
    my_assigned = [c for c in all_complaints if c.get("assigned_agent") == current_user["full_name"]]
    
    pending_action = [c for c in all_complaints if c["status"] in ["Submitted", "Processing", "In Review"]]

    return {
        "agent_name": current_user["full_name"],
        "metrics": {
            "queue_total": len(all_complaints),
            "unassigned_cases": len(unassigned),
            "my_assigned_cases": len(my_assigned),
            "pending_action": len(pending_action)
        },
        "my_assigned_complaints": my_assigned,
        "queue_complaints": pending_action
    }

@router.get("/reviewer")
def get_reviewer_dashboard(current_user: dict = Depends(require_role("Reviewer", "Manager", "Admin", "Administrator"))):
    flagged_complaints = [
        c for c in COMPLAINTS_STORE 
        if c.get("has_hallucination") 
        or not c.get("python_validation_passed", True) 
        or c.get("status") == "Escalated"
    ]

    return {
        "metrics": {
            "flagged_items_count": len(flagged_complaints),
            "hallucinations_detected": len([c for c in flagged_complaints if c.get("has_hallucination")]),
            "validation_failures": len([c for c in flagged_complaints if not c.get("python_validation_passed", True)])
        },
        "review_queue": flagged_complaints
    }

@router.get("/manager")
def get_manager_dashboard(current_user: dict = Depends(require_role("Manager", "Admin", "Administrator"))):
    all_c = list(COMPLAINTS_STORE)
    total = len(all_c)
    resolved = len([c for c in all_c if c["status"] == "Resolved"])
    escalated = len([c for c in all_c if c["status"] == "Escalated"])
    total_approved = sum([c.get("approved_credit", 0.0) for c in all_c])
    
    by_category: Dict[str, int] = {}
    for c in all_c:
        cat = c["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    by_department: Dict[str, int] = {}
    for c in all_c:
        dept = c.get("assigned_department", "Unassigned") or "Unassigned"
        by_department[dept] = by_department.get(dept, 0) + 1

    return {
        "metrics": {
            "total_complaints": total,
            "resolution_rate": round((resolved / total * 100) if total else 0, 1),
            "escalation_count": escalated,
            "total_financial_credits": round(total_approved, 2),
            "sla_compliance_percent": 94.5
        },
        "by_category": by_category,
        "by_department": by_department,
        "recent_activity": AUDIT_LOGS_STORE[-10:]
    }

@router.get("/admin")
def get_admin_dashboard(current_user: dict = Depends(require_role("Admin", "Administrator"))):
    return {
        "system_status": "Healthy",
        "metrics": {
            "total_users": 5,
            "kb_documents_count": len(KNOWLEDGE_BASE_STORE),
            "rule_matrix_count": len(RULE_MATRIX_STORE),
            "audit_logs_count": len(AUDIT_LOGS_STORE)
        },
        "knowledge_documents": KNOWLEDGE_BASE_STORE,
        "rule_matrix": RULE_MATRIX_STORE,
        "audit_logs": AUDIT_LOGS_STORE[-15:]
    }
