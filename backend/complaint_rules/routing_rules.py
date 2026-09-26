"""
Routing Rules Engine for SupportNova Pipeline 2.
Determines primary and supporting departments for multi-issue complaints.
"""

from typing import List, Dict, Any, Tuple
from backend.complaint_rules.rule_matrix import DEFAULT_DEPARTMENT_ROUTING

DEPARTMENT_KEYWORD_MAP = {
    "Safety": ["fire", "hazard", "burn", "electric shock", "injury", "poison", "explode", "smoke", "sparks"],
    "Compliance": ["data breach", "privacy leak", "stolen password", "hacked", "gdpr", "legal", "lawyer", "lawsuit", "suing"],
    "Billing": ["charge", "billed", "credit card", "invoice", "duplicate charge", "overcharged", "payment", "bank"],
    "Logistics": ["delayed", "courier", "package", "tracking", "lost package", "address", "shipping", "delivery"],
    "Returns": ["broken", "damaged", "shattered", "defect", "missing parts", "return", "refund"],
    "Warranty": ["warranty", "claim", "repair", "expired warranty", "guarantee"],
    "Account Security": ["password", "account locked", "unauthorized access", "2fa", "login failure"],
    "Technical Support": ["firmware", "app crash", "sync failure", "pairing error", "software bug"]
}

def determine_routing(
    complaint_title: str,
    complaint_description: str,
    primary_category: str
) -> Tuple[str, List[str]]:
    """
    Determines primary department and supporting departments for multi-issue complaints.
    """
    text_lower = (complaint_title + " " + complaint_description).lower()
    
    primary_dept = DEFAULT_DEPARTMENT_ROUTING.get(primary_category, "Customer Relations")
    supporting_depts = []

    # Check for multi-issue keywords
    for dept, keywords in DEPARTMENT_KEYWORD_MAP.items():
        if dept != primary_dept:
            if any(kw in text_lower for kw in keywords):
                if dept not in supporting_depts:
                    supporting_depts.append(dept)

    return primary_dept, supporting_depts
