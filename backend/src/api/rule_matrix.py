"""
Rule Matrix API Router (Admin Ground-Truth Business Rule Engine)
Provides full admin-only CRUD, validation against active policies/configs,
soft-delete, audit trails, and execution matching endpoint.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.schemas.schemas import RuleMatrixItem, RuleMatrixCreate, RuleMatrixUpdate, RuleMatrixAuditResponse
from backend.security.jwt_auth import get_current_user, require_role
from backend.src.store import (
    RULE_MATRIX_STORE,
    RULE_MATRIX_AUDIT_STORE,
    KNOWLEDGE_BASE_STORE,
    CATEGORIES_CONFIG,
    DEPARTMENTS_CONFIG
)
from backend.complaint_rules.engine import RuleMatrixEngine

router = APIRouter(prefix="/admin/rule-matrix", tags=["Admin Rule Matrix"])
public_router = APIRouter(prefix="/rule_matrix", tags=["Rule Matrix Public"])


def validate_rule_payload(category: str, subcategory: str, department: str, policy_id: str):
    """Defensive validation against active KB documents, categories config, and departments config."""
    # 1. Validate policy_id exists and is Active in KNOWLEDGE_BASE_STORE
    kb_doc = None
    for doc in KNOWLEDGE_BASE_STORE:
        if doc.get("document_id") == policy_id:
            kb_doc = doc
            break

    if not kb_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Policy ID '{policy_id}' does not exist in Knowledge Base."
        )

    doc_status = kb_doc.get("status", "").lower()
    if doc_status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Policy '{policy_id}' is currently in '{kb_doc.get('status')}' status. Rules may only reference 'Active' policies."
        )

    # 2. Validate category & subcategory exist in categories.json
    valid_categories = CATEGORIES_CONFIG.get("categories", [])
    cat_match = None
    for cat in valid_categories:
        if cat.get("name", "").lower() == category.lower() or cat.get("code", "").lower() == category.lower():
            cat_match = cat
            break

    if not cat_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Category '{category}' is invalid."
        )

    subcats = cat_match.get("subcategories", [])
    subcat_match = any(
        sub.get("name", "").lower() == subcategory.lower() or sub.get("code", "").lower() == subcategory.lower()
        for sub in subcats
    )
    if not subcat_match and subcategory:
        # Check if subcategory exists in any category
        subcat_match_any = False
        for c in valid_categories:
            for s in c.get("subcategories", []):
                if s.get("name", "").lower() == subcategory.lower() or s.get("code", "").lower() == subcategory.lower():
                    subcat_match_any = True
                    break
        if not subcat_match_any:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation Error: Subcategory '{subcategory}' is invalid."
            )

    # 3. Validate department exists in departments.json
    valid_departments = DEPARTMENTS_CONFIG.get("departments", [])
    dept_match = any(
        d.get("name", "").lower() == department.lower() or
        d.get("short_name", "").lower() == department.lower() or
        d.get("code", "").lower() == department.lower() or
        d.get("id", "").lower() == department.lower()
        for d in valid_departments
    )
    if not dept_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation Error: Department '{department}' is invalid."
        )


@router.get("")
def list_rule_matrix(
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    escalation_required: Optional[bool] = Query(None),
    include_inactive: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve paginated and filterable rule matrix table."""
    results = []
    for rule in RULE_MATRIX_STORE:
        # Default: filter active rules unless include_inactive=True
        if not include_inactive and not rule.get("is_active", True):
            continue

        if category and rule.get("category", "").lower() != category.lower():
            continue

        if department and rule.get("department", "").lower() != department.lower():
            continue

        if urgency and rule.get("urgency", "").lower() != urgency.lower():
            continue

        if escalation_required is not None and rule.get("escalation_required") != escalation_required:
            continue

        if search:
            q = search.lower()
            r_id = rule.get("rule_id", "").lower()
            r_cat = rule.get("category", "").lower()
            r_sub = rule.get("subcategory", "").lower()
            r_dept = rule.get("department", "").lower()
            if q not in r_id and q not in r_cat and q not in r_sub and q not in r_dept:
                continue

        results.append(rule)

    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    paginated_items = results[start:end]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": paginated_items
    }


@router.post("", response_model=RuleMatrixItem, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleMatrixCreate,
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
):
    """Create a new rule with defensive active policy and config validation."""
    validate_rule_payload(
        category=payload.category,
        subcategory=payload.subcategory,
        department=payload.department,
        policy_id=payload.policy_id
    )

    rule_id = payload.rule_id
    if not rule_id:
        rule_id = f"RULE-{(len(RULE_MATRIX_STORE) + 1):04d}"

    # Check rule_id unique
    for r in RULE_MATRIX_STORE:
        if r.get("rule_id") == rule_id:
            rule_id = f"RULE-{(len(RULE_MATRIX_STORE) + 101):04d}"

    now_iso = datetime.now(timezone.utc).isoformat()
    new_rule = {
        "rule_id": rule_id,
        "category": payload.category,
        "subcategory": payload.subcategory,
        "conditions": payload.conditions,
        "department": payload.department,
        "supporting_departments": payload.supporting_departments or [],
        "urgency": payload.urgency,
        "priority": payload.priority,
        "policy_id": payload.policy_id,
        "escalation_required": payload.escalation_required,
        "escalation_level": payload.escalation_level,
        "required_actions": payload.required_actions or [],
        "prohibited_actions": payload.prohibited_actions or [],
        "follow_up_required": payload.follow_up_required,
        "is_active": True,
        "created_by": current_user.get("email", "admin@nexalink.com"),
        "created_at": now_iso,
        "updated_at": now_iso
    }

    RULE_MATRIX_STORE.insert(0, new_rule)

    # Immutable Audit Log
    RULE_MATRIX_AUDIT_STORE.append({
        "id": len(RULE_MATRIX_AUDIT_STORE) + 1,
        "rule_id": rule_id,
        "action": "CREATE",
        "previous_state": None,
        "new_state": new_rule,
        "changed_by": current_user.get("email", "admin@nexalink.com"),
        "changed_at": now_iso
    })

    return new_rule


@router.put("/{rule_id}", response_model=RuleMatrixItem)
def update_rule(
    rule_id: str,
    payload: RuleMatrixUpdate,
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
):
    """Update an existing rule with validation and immutable audit entry."""
    target_idx = -1
    target_rule = None
    for idx, r in enumerate(RULE_MATRIX_STORE):
        if r.get("rule_id") == rule_id:
            target_idx = idx
            target_rule = r
            break

    if not target_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID '{rule_id}' not found.")

    new_cat = payload.category if payload.category is not None else target_rule.get("category")
    new_sub = payload.subcategory if payload.subcategory is not None else target_rule.get("subcategory")
    new_dept = payload.department if payload.department is not None else target_rule.get("department")
    new_pol = payload.policy_id if payload.policy_id is not None else target_rule.get("policy_id")

    validate_rule_payload(
        category=new_cat,
        subcategory=new_sub,
        department=new_dept,
        policy_id=new_pol
    )

    prev_state = dict(target_rule)
    now_iso = datetime.now(timezone.utc).isoformat()

    if payload.category is not None: target_rule["category"] = payload.category
    if payload.subcategory is not None: target_rule["subcategory"] = payload.subcategory
    if payload.conditions is not None: target_rule["conditions"] = payload.conditions
    if payload.department is not None: target_rule["department"] = payload.department
    if payload.supporting_departments is not None: target_rule["supporting_departments"] = payload.supporting_departments
    if payload.urgency is not None: target_rule["urgency"] = payload.urgency
    if payload.priority is not None: target_rule["priority"] = payload.priority
    if payload.policy_id is not None: target_rule["policy_id"] = payload.policy_id
    if payload.escalation_required is not None: target_rule["escalation_required"] = payload.escalation_required
    if payload.escalation_level is not None: target_rule["escalation_level"] = payload.escalation_level
    if payload.required_actions is not None: target_rule["required_actions"] = payload.required_actions
    if payload.prohibited_actions is not None: target_rule["prohibited_actions"] = payload.prohibited_actions
    if payload.follow_up_required is not None: target_rule["follow_up_required"] = payload.follow_up_required
    if payload.is_active is not None: target_rule["is_active"] = payload.is_active
    target_rule["updated_at"] = now_iso

    # Audit log
    RULE_MATRIX_AUDIT_STORE.append({
        "id": len(RULE_MATRIX_AUDIT_STORE) + 1,
        "rule_id": rule_id,
        "action": "UPDATE",
        "previous_state": prev_state,
        "new_state": dict(target_rule),
        "changed_by": current_user.get("email", "admin@nexalink.com"),
        "changed_at": now_iso
    })

    return target_rule


@router.delete("/{rule_id}")
def deactivate_rule(
    rule_id: str,
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
):
    """Soft-delete (deactivate) a rule by setting is_active=False. Never hard-deletes."""
    target_rule = None
    for r in RULE_MATRIX_STORE:
        if r.get("rule_id") == rule_id:
            target_rule = r
            break

    if not target_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule ID '{rule_id}' not found.")

    prev_state = dict(target_rule)
    now_iso = datetime.now(timezone.utc).isoformat()
    target_rule["is_active"] = False
    target_rule["updated_at"] = now_iso

    RULE_MATRIX_AUDIT_STORE.append({
        "id": len(RULE_MATRIX_AUDIT_STORE) + 1,
        "rule_id": rule_id,
        "action": "DEACTIVATE",
        "previous_state": prev_state,
        "new_state": dict(target_rule),
        "changed_by": current_user.get("email", "admin@nexalink.com"),
        "changed_at": now_iso
    })

    return {
        "message": f"Rule '{rule_id}' deactivated successfully.",
        "rule_id": rule_id,
        "is_active": False
    }


@router.get("/{rule_id}/audit-log", response_model=List[RuleMatrixAuditResponse])
def get_rule_audit_log(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retrieve complete audit trail for a specific rule."""
    audit_chain = [
        entry for entry in RULE_MATRIX_AUDIT_STORE
        if entry.get("rule_id") == rule_id
    ]
    return audit_chain


@router.post("/match")
def match_complaint_features(
    features: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Execute RuleMatrixEngine against arbitrary complaint features for testing/auditing."""
    engine = RuleMatrixEngine()
    matched = engine.match(features)
    if not matched:
        return {"matched": False, "rule": None}
    
    return {
        "matched": True,
        "rule": matched.__dict__
    }


# Public router for backward compatibility with frontend get_rule_matrix
@public_router.get("", response_model=List[RuleMatrixItem])
def get_rule_matrix_public(current_user: dict = Depends(get_current_user)):
    return [r for r in RULE_MATRIX_STORE if r.get("is_active", True)]
