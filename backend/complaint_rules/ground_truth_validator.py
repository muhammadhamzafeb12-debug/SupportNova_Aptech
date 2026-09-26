"""
Ground-Truth Validation Orchestrator for SupportNova Pipeline 2.
Executes deterministic Python business logic without relying on any LLM.
Strips prompt injection directives from untrusted input text.
"""

import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.models import RuleMatrix, EscalationLevel, Policy
from backend.schemas.schemas import GenAIResponseSchema, PythonValidationSchema
from backend.complaint_rules.rule_matrix import RULE_MATRIX_DATA
from backend.complaint_rules.routing_rules import determine_routing
from backend.complaint_rules.escalation_rules import evaluate_escalation
from backend.complaint_rules.eligibility_rules import evaluate_eligibility
from backend.complaint_rules.sla_rules import calculate_sla_deadlines
from backend.complaint_rules.policy_precedence import validate_policy_grounding, resolve_policy_precedence

UNSUPPORTED_PROMISE_PATTERNS = [
    r"guaranteed refund",
    r"guaranteed compensation",
    r"100% money back immediately",
    r"unconditional replacement",
    r"free lifetime warranty",
    r"instant payment",
    r"no questions asked refund",
    r"delivery within 1 hour",
    r"unauthorized cash payout"
]

def sanitize_untrusted_input(text: str) -> str:
    """
    Sanitizes untrusted complaint text and documents to prevent prompt injection directives
    from affecting deterministic Python evaluation.
    """
    if not text:
        return ""
    # Strip prompt injection directives
    injection_patterns = [
        r"ignore (all )?previous instructions.*",
        r"ignore your rules.*",
        r"system administrator says.*",
        r"use this fake policy.*",
        r"you are now an automated.*",
        r"override system configuration.*"
    ]
    cleaned_text = text
    for pat in injection_patterns:
        cleaned_text = re.sub(pat, "", cleaned_text, flags=re.IGNORECASE)
    return cleaned_text

def run_ground_truth_validation(
    db: Session,
    complaint_title: str,
    complaint_description: str,
    genai_output: Optional[GenAIResponseSchema] = None,
    customer_type: str = "REGULAR",
    prev_complaint_ref: Optional[str] = None,
    warranty_status: str = "ACTIVE",
    defect_condition: Optional[str] = None,
    order_days_ago: int = 10,
    complaint_id_str: str = "CMP-TEMP"
) -> PythonValidationSchema:
    """
    Pipeline 2: Independent Python Ground-Truth Engine.
    Executes 100% deterministic Python rules without any LLM calls.
    """
    # 1. Sanitize untrusted input text to neutralize prompt injection directives
    safe_title = sanitize_untrusted_input(complaint_title)
    safe_desc = sanitize_untrusted_input(complaint_description)
    combined_text = (safe_title + " " + safe_desc).lower()

    # 2. Category & Subcategory Detection from high-risk overrides, DB Rule Matrix, or static fallback
    matched_rule_id = "RULE-001"
    verified_category = "Service Quality"
    verified_subcategory = "General Inquiry"

    # Priority 1: High-risk category overrides
    if any(k in combined_text for k in ["fire", "hazard", "burn", "electric shock", "injury", "poison", "explode", "smoke", "sparks", "battery", "swollen", "overheating"]):
        verified_category = "Safety"
        verified_subcategory = "Hazardous Product Incident"
        matched_rule_id = "RULE-SAF-001"
    elif any(k in combined_text for k in ["data breach", "privacy leak", "stolen password", "hacked", "gdpr", "privacy"]):
        verified_category = "Privacy"
        verified_subcategory = "Data Breach / Unauthorized Access"
        matched_rule_id = "RULE-PRV-001"
    elif any(k in combined_text for k in ["lawyer", "lawsuit", "suing", "attorney", "legal action"]):
        verified_category = "Legal Threat"
        verified_subcategory = "Pending Litigation Notice"
        matched_rule_id = "RULE-LEG-001"
    else:
        # Priority 2: Query DB rule matrix
        db_rules = db.query(RuleMatrix).filter(RuleMatrix.is_active == True).all() if db else []
        matched_db_rule: Optional[RuleMatrix] = None

        if db_rules:
            for rule in db_rules:
                conds = [c.strip().lower() for c in rule.conditions.split(",")]
                if any(c in combined_text for c in conds if len(c) > 3):
                    matched_db_rule = rule
                    break

        if matched_db_rule:
            matched_rule_id = matched_db_rule.rule_id
            verified_category = matched_db_rule.category
            verified_subcategory = matched_db_rule.subcategory
        else:
            # Priority 3: Static keyword fallbacks
            if any(k in combined_text for k in ["duplicate charge", "overcharged", "double charge", "charged twice", "charge", "billed"]):
                verified_category = "Billing"
                verified_subcategory = "Duplicate Charge"
                matched_rule_id = "RULE-BIL-001"
            elif any(k in combined_text for k in ["broken", "damaged", "shattered", "defect"]):
                verified_category = "Product Defect"
                verified_subcategory = "Physical Damage"
                matched_rule_id = "RULE-DEF-001"
            elif any(k in combined_text for k in ["delayed", "courier", "package missing"]):
                verified_category = "Delivery"
                verified_subcategory = "Delayed Delivery"
                matched_rule_id = "RULE-DEL-001"

    # 3. Routing Engine (Primary & Supporting Departments)
    verified_dept, supporting_depts = determine_routing(safe_title, safe_desc, verified_category)

    # 4. Escalation Engine (Evaluates Safety, Privacy, Security, Legal, Repeat, High Value)
    esc_req, esc_lvl, esc_reason, verified_urg, verified_prio = evaluate_escalation(
        safe_title, safe_desc, verified_category, customer_type, prev_complaint_ref
    )

    # 5. Eligibility Engine (Refund, Replacement, Compensation)
    refund_elig, replacement_elig, comp_elig, elig_reasons = evaluate_eligibility(
        safe_title, safe_desc, verified_category, verified_subcategory,
        customer_type, warranty_status, defect_condition, order_days_ago
    )

    # 6. SLA Engine
    sla_h, resp_dl, resol_dl = calculate_sla_deadlines(verified_prio, verified_dept)

    # 7. Policy Precedence & Policy Validation
    cited_refs = genai_output.policy_references if genai_output else []
    pol_valid, pol_id, pol_sec, policy_issues = validate_policy_grounding(db, cited_refs, verified_category)

    # 8. Mandatory & Prohibited Actions
    mandatory_actions = [
        f"Acknowledge complaint within {sla_h}h SLA window.",
        "Verify customer account & order details in ERP.",
        f"Apply {verified_category} SOP guidelines under {pol_id}."
    ]
    prohibited_actions = [
        "Do not issue unauthorized cash refunds exceeding $500 without manager sign-off.",
        "Do not promise delivery within 1 hour.",
        "Do not grant unapproved lifetime warranty extensions."
    ]

    # 9. GenAI Output Checks (Hallucinations, Unsupported Claims, Contradictions, Missing Actions)
    unsupported_claims = []
    contradictions = []
    missing_actions = []

    if genai_output:
        resp_text = (genai_output.customer_response or "").lower()
        for pat in UNSUPPORTED_PROMISE_PATTERNS:
            if re.search(pat, resp_text):
                unsupported_claims.append(f"GenAI customer response contains prohibited guarantee: '{pat}'")

        if genai_output.category.lower() != verified_category.lower() and verified_category in ["Safety", "Privacy"]:
            contradictions.append(f"GenAI predicted category '{genai_output.category}' for high-risk issue, but Python rules mandate '{verified_category}'.")

        if genai_output.escalation_required != esc_req:
            contradictions.append(f"GenAI escalation ({genai_output.escalation_required}) contradicts Python ground-truth escalation ({esc_req}).")

        # Check mandatory actions
        genai_steps = " ".join(genai_output.resolution_steps or []).lower()
        for act in mandatory_actions:
            act_words = [w for w in re.findall(r'\w+', act.lower()) if len(w) > 4]
            if not any(w in genai_steps for w in act_words):
                missing_actions.append(f"Mandatory action missing in GenAI resolution steps: '{act}'")

    policy_grounding_valid = len(unsupported_claims) == 0 and len(contradictions) == 0 and len(policy_issues) == 0

    return PythonValidationSchema(
        complaint_id=genai_output.complaint_id if genai_output else complaint_id_str,
        rule_id_matched=matched_rule_id,
        verified_category=verified_category,
        verified_subcategory=verified_subcategory,
        verified_department=verified_dept,
        supporting_departments=supporting_depts,
        verified_urgency=verified_urg,
        verified_priority=verified_prio,
        verified_escalation_required=esc_req,
        verified_escalation_level=esc_lvl,
        verified_escalation_reason=esc_reason,
        verified_refund_eligible=refund_elig,
        verified_replacement_eligible=replacement_elig,
        verified_compensation_eligible=comp_elig,
        verified_sla_hours=sla_h,
        verified_policy_id=pol_id,
        verified_policy_section=pol_sec,
        mandatory_actions=mandatory_actions,
        prohibited_actions=prohibited_actions,
        policy_grounding_valid=policy_grounding_valid,
        unsupported_claims=unsupported_claims,
        contradictions=contradictions,
        missing_actions=missing_actions
    )
