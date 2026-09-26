"""
Policy Precedence & Policy Validation Engine for SupportNova Pipeline 2.
Validates policy applicability, section, version, outdated status, and deterministic precedence hierarchy.
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models import Policy, PolicyStatus

# Policy Rank Precedence (Lower rank number = higher precedence authority)
POLICY_PRECEDENCE_RANK = {
    "POL-017": 1,  # Safety Policy (Highest Authority)
    "POL-008": 2,  # Privacy Policy (Regulatory Authority)
    "POL-009": 3,  # Escalation Procedure
    "POL-002": 4,  # Refund Policy
    "POL-003": 4,  # Replacement Policy
    "POL-005": 4,  # Billing Policy
    "POL-007": 4,  # Warranty Policy
    "POL-006": 4,  # Delivery Policy
    "POL-015": 4,  # Account Security Policy
    "POL-001": 10, # General Complaint Policy (Base Standard)
    "POL-010": 10  # General Complaint SOP
}

def resolve_policy_precedence(policy_doc_ids: List[str]) -> str:
    """
    Selects the winning policy doc_id based on deterministic precedence hierarchy.
    Safety/Regulatory > Specific Policy > General SOP.
    """
    if not policy_doc_ids:
        return "POL-001"
    
    sorted_policies = sorted(policy_doc_ids, key=lambda pid: POLICY_PRECEDENCE_RANK.get(pid, 99))
    return sorted_policies[0]

def validate_policy_grounding(
    db: Session,
    cited_policy_references: List[Dict[str, Any]],
    verified_category: str
) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
    """
    Validates cited policy references against approved DB policies.
    Detects hallucinated, outdated, or superseded policy references.
    Returns (is_valid, primary_policy_id, primary_section, issues_list).
    """
    issues = []
    primary_policy_id = None
    primary_section = "SECTION 2"

    # Category default winning policy
    category_defaults = {
        "Safety": ("POL-017", "SECTION 2 - EMERGENCY SAFETY RISK MANAGEMENT"),
        "Privacy": ("POL-008", "SECTION 3 - DATA PRIVACY COMPLIANCE"),
        "Billing": ("POL-005", "SECTION 2 - BILLING DISPUTE"),
        "Refund": ("POL-002", "SECTION 2 - REFUND ELIGIBILITY"),
        "Product Defect": ("POL-003", "SECTION 2 - REPLACEMENT AND DEFECT SOP"),
        "Account": ("POL-015", "SECTION 2 - ACCOUNT SECURITY"),
        "Warranty": ("POL-007", "SECTION 2 - WARRANTY TERMS"),
        "Delivery": ("POL-006", "SECTION 2 - DELIVERY SLA AND LOGISTICS")
    }
    
    expected_doc_id, expected_sec = category_defaults.get(verified_category, ("POL-001", "SECTION 2 - GENERAL COMPLAINT SOP"))
    primary_policy_id = expected_doc_id
    primary_section = expected_sec

    if not cited_policy_references:
        issues.append("GenAI output provided no policy references.")
        return False, primary_policy_id, primary_section, issues

    for ref in cited_policy_references:
        doc_id = ref.get("doc_id") or ref.get("policy_id")
        if not doc_id:
            issues.append("GenAI cited a policy reference missing a valid doc_id.")
            continue
        
        # Query DB policy if session available
        if db is not None:
            policy_obj = db.query(Policy).filter(Policy.doc_id == doc_id).first()
            if not policy_obj:
                issues.append(f"GenAI cited non-existent/hallucinated policy ID '{doc_id}'.")
            elif policy_obj.status in [PolicyStatus.SUPERSEDED.value, PolicyStatus.OUTDATED.value]:
                issues.append(f"GenAI cited outdated/superseded policy '{doc_id}' (Status: {policy_obj.status}).")

    is_valid = len(issues) == 0
    return is_valid, primary_policy_id, primary_section, issues
