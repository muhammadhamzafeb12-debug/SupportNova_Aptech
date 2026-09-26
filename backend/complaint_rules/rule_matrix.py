"""
Structured Complaint Resolution Rule Matrix containing 100+ deterministic business rules.
Independent from GenAI, providing ground-truth criteria for NovaCart Technologies.
"""

from typing import List, Dict, Any, Optional

CATEGORIES_MAP = {
    "Product Defect": ["Physical Damage", "Malfunctioning Hardware", "Missing Components", "Counterfeit Item"],
    "Billing": ["Duplicate Charge", "Incorrect Charge", "Refund Missing", "Subscription Renewal Error"],
    "Delivery": ["Delayed Delivery", "Wrong Address", "Damaged Package", "Missing Package"],
    "Refund": ["Refund Delay", "Refund Rejected", "Partial Refund", "Unauthorized Deductions"],
    "Account": ["Account Locked", "Unauthorized Access", "Password Reset Failure", "Profile Data Error"],
    "Technical Support": ["Firmware Crash", "App Disconnection", "Sync Failure", "Pairing Error"],
    "Service Quality": ["Rude Staff", "Unhelpful Response", "Long Wait Time", "Misleading Information"],
    "Warranty": ["Warranty Expiry Dispute", "Claim Rejection", "Repair Delay", "Parts Unavailable"],
    "Privacy": ["Data Leak", "Unauthorized Data Sharing", "GDPR Removal Request", "Spam Email Complaint"],
    "Safety": ["Hazardous Product Incident", "Electric Shock", "Overheating/Fire Risk", "Chemical Leak"]
}

DEFAULT_DEPARTMENT_ROUTING = {
    "Product Defect": "Returns",
    "Billing": "Billing",
    "Delivery": "Logistics",
    "Refund": "Returns",
    "Account": "Account Security",
    "Technical Support": "Technical Support",
    "Service Quality": "Customer Relations",
    "Warranty": "Warranty",
    "Privacy": "Compliance",
    "Safety": "Safety"
}

def generate_100_plus_rules() -> List[Dict[str, Any]]:
    """Generates 100+ structured rules with explicit business logic fields."""
    rules = []
    rule_counter = 1

    # 1. Base 100 Rules generated systematically across 10 categories x subcategories x variants
    variants = [
        ("Standard", "Low", "P3 – Low", False, "No Escalation", 24),
        ("Escalated", "High", "P1 – High", True, "Supervisor Review", 12),
        ("Critical", "Critical", "P0 – Critical", True, "Critical Management Escalation", 4)
    ]

    for cat_name, subcategories in CATEGORIES_MAP.items():
        dept = DEFAULT_DEPARTMENT_ROUTING[cat_name]
        for sub_name in subcategories:
            for var_label, default_urg, default_prio, esc_req, esc_lvl, default_sla in variants:
                r_id = f"RULE-{rule_counter:03d}"
                
                # Category specific overrides
                urgency = default_urg
                priority = default_prio
                escalation_required = esc_req
                escalation_level = esc_lvl
                sla_hours = default_sla
                
                if cat_name == "Safety":
                    urgency = "Critical"
                    priority = "P0 – Critical"
                    escalation_required = True
                    escalation_level = "Critical Management Escalation"
                    sla_hours = 2
                    policy_id = "POL-017"
                    policy_sec = "SECTION 2 - EMERGENCY SAFETY RISK MANAGEMENT"
                elif cat_name == "Privacy":
                    urgency = "High"
                    priority = "P1 – High"
                    escalation_required = True
                    escalation_level = "Compliance Review"
                    sla_hours = 6
                    policy_id = "POL-008"
                    policy_sec = "SECTION 3 - DATA PRIVACY COMPLIANCE"
                elif cat_name == "Account":
                    policy_id = "POL-015"
                    policy_sec = "SECTION 2 - ACCOUNT SECURITY"
                elif cat_name == "Refund":
                    policy_id = "POL-002"
                    policy_sec = "SECTION 2 - REFUND ELIGIBILITY"
                elif cat_name == "Product Defect":
                    policy_id = "POL-003"
                    policy_sec = "SECTION 2 - REPLACEMENT AND DEFECT SOP"
                elif cat_name == "Billing":
                    policy_id = "POL-005"
                    policy_sec = "SECTION 2 - BILLING DISPUTE"
                elif cat_name == "Warranty":
                    policy_id = "POL-007"
                    policy_sec = "SECTION 2 - WARRANTY TERMS"
                elif cat_name == "Delivery":
                    policy_id = "POL-006"
                    policy_sec = "SECTION 2 - DELIVERY SLA AND LOGISTICS"
                else:
                    policy_id = "POL-001"
                    policy_sec = "SECTION 2 - GENERAL COMPLAINT SOP"

                # Eligibility logic flags
                refund_eligible = cat_name in ["Billing", "Refund", "Product Defect"] and var_label != "Critical"
                replacement_eligible = cat_name in ["Product Defect", "Warranty", "Delivery"]
                compensation_eligible = (cat_name in ["Safety", "Delivery", "Service Quality"] and var_label in ["Escalated", "Critical"])
                
                req_actions = [
                    f"Acknowledge complaint within {sla_hours} hour SLA window.",
                    f"Verify customer order details and product ID in ERP.",
                    f"Apply {cat_name} standard operating procedure under {policy_id}."
                ]
                
                prohib_actions = [
                    "Do not issue unauthorized cash refund exceeding $500 without manager approval.",
                    "Do not promise guaranteed delivery within 1 hour.",
                    "Do not offer lifetime warranty without explicit policy documentation."
                ]

                rules.append({
                    "rule_id": r_id,
                    "category": cat_name,
                    "subcategory": sub_name,
                    "conditions": f"{cat_name.lower()}, {sub_name.lower()}, {var_label.lower()}",
                    "department": dept,
                    "urgency": urgency,
                    "priority": priority,
                    "policy_doc_id": policy_id,
                    "policy_section": policy_sec,
                    "escalation_required": escalation_required,
                    "escalation_level": escalation_level,
                    "required_actions": req_actions,
                    "prohibited_actions": prohib_actions,
                    "refund_eligibility": refund_eligible,
                    "replacement_eligibility": replacement_eligible,
                    "compensation_eligibility": compensation_eligible,
                    "follow_up_required": True,
                    "sla_hours": sla_hours,
                    "rule_priority": rule_counter,
                    "is_active": True,
                    "version": "1.0"
                })
                rule_counter += 1

    # Ensure total rules count is at least 120+
    return rules

# Pre-instantiated static rule set for fast non-DB lookup in pure unit tests
RULE_MATRIX_DATA = generate_100_plus_rules()
