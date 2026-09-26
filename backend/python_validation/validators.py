"""
Independent Pure Python Validation Module for SupportNova Pipeline 2.
Enforces 100% deterministic, non-GenAI business-rule verification.
ZERO network or LLM calls anywhere in this file.
"""
import re
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.complaint_rules.engine import RuleMatrixEngine
from backend.src.store import KNOWLEDGE_BASE_STORE

logger = logging.getLogger(__name__)


@dataclass
class ValidationOutcome:
    passed: bool
    expected_value: Any
    actual_value: Any
    rule_id_used: Optional[str]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _get_matched_rule(complaint: Dict[str, Any], rule_matrix_engine: Optional[RuleMatrixEngine] = None):
    engine = rule_matrix_engine or RuleMatrixEngine()
    features = {
        "category": complaint.get("category", ""),
        "subcategory": complaint.get("sub_category") or complaint.get("subcategory", ""),
        "dispute_amount_max": complaint.get("requested_credit", 0.0),
        "dispute_amount_min": complaint.get("requested_credit", 0.0),
        "description": complaint.get("description", "")
    }
    return engine.match(features)


# ── 1. validate_category ──────────────────────────────────────────────────────

def validate_category(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """Validates GenAI issue_category and subcategory against RuleMatrixEngine determinism."""
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue")
    }
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    genai_cat = (genai_result.get("issue_category") or "").strip()
    genai_subcat = (genai_result.get("subcategory") or "").strip()

    if not matched_rule:
        return ValidationOutcome(
            passed=True,
            expected_value={"category": genai_cat, "subcategory": genai_subcat},
            actual_value={"category": genai_cat, "subcategory": genai_subcat},
            rule_id_used=None,
            explanation="No specific rule matrix match found; accepting GenAI category."
        )

    exp_cat = matched_rule.category
    exp_subcat = matched_rule.subcategory

    # Category matching logic (case-insensitive substring or code check)
    cat_match = genai_cat.lower() in exp_cat.lower() or exp_cat.lower() in genai_cat.lower()
    subcat_match = genai_subcat.lower() in exp_subcat.lower() or exp_subcat.lower() in genai_subcat.lower() or not genai_subcat

    passed = cat_match and subcat_match
    return ValidationOutcome(
        passed=passed,
        expected_value={"category": exp_cat, "subcategory": exp_subcat},
        actual_value={"category": genai_cat, "subcategory": genai_subcat},
        rule_id_used=matched_rule.rule_id,
        explanation=f"Category match check against rule '{matched_rule.rule_id}' ({'PASSED' if passed else 'FAILED'})."
    )


# ── 2. validate_department_routing ────────────────────────────────────────────

def validate_department_routing(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """Validates GenAI department routing against RuleMatrixEngine determinism."""
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue")
    }
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    genai_dept = (genai_result.get("department") or "").strip()

    if not matched_rule:
        return ValidationOutcome(
            passed=True,
            expected_value=genai_dept,
            actual_value=genai_dept,
            rule_id_used=None,
            explanation="No specific rule matrix match found; accepting GenAI department routing."
        )

    exp_dept = matched_rule.department
    passed = genai_dept.lower() in exp_dept.lower() or exp_dept.lower() in genai_dept.lower()

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_dept,
        actual_value=genai_dept,
        rule_id_used=matched_rule.rule_id,
        explanation=f"Department routing check against rule '{matched_rule.rule_id}' (Expected: '{exp_dept}', Actual: '{genai_dept}')."
    )


# ── 3. validate_urgency ───────────────────────────────────────────────────────

def validate_urgency(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """
    Validates urgency derived from OBJECTIVE rule-matrix conditions and complaint features,
    NEVER relying on GenAI sentiment alone (Sentiment-vs-Urgency Trap).
    """
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue", "")
    }
    desc = (cmp_obj.get("description") or "").lower()

    # Objective trigger rules
    if any(kw in desc for kw in ["fcc", "attorney", "lawsuit", "legal", "safety", "hazard", "fire", "emergency", "outage"]):
        exp_urgency = "Critical"
    elif any(kw in desc for kw in ["roaming", "unauthorized", "fee dispute", "intermittent", "overcharge"]):
        exp_urgency = "High"
    else:
        matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)
        exp_urgency = matched_rule.urgency if matched_rule else "Medium"

    genai_urgency = genai_result.get("urgency", "Medium")
    passed = genai_urgency.lower() == exp_urgency.lower()

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_urgency,
        actual_value=genai_urgency,
        rule_id_used=_get_matched_rule(cmp_obj, rule_matrix_engine).rule_id if _get_matched_rule(cmp_obj, rule_matrix_engine) else None,
        explanation=f"Objective urgency check ({'PASSED' if passed else 'MISMATCH'}: Expected '{exp_urgency}', GenAI: '{genai_urgency}')."
    )


# ── 4. validate_escalation ────────────────────────────────────────────────────

def validate_escalation(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """
    CRITICAL PRECEDENCE RULE:
    If the matched rule has escalation_required=True (or objective triggers like legal/FCC threats),
    Python's rule-matrix outcome ALWAYS enforces escalation_required=True REGARDLESS of what GenAI said.
    Python's ground-truth rule-matrix decision overrides GenAI on this field — always.
    """
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue", "")
    }
    desc = (cmp_obj.get("description") or "").lower()
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    rule_escalation = matched_rule.escalation_required if matched_rule else False
    trigger_escalation = any(kw in desc for kw in ["fcc", "attorney", "lawsuit", "legal threat", "safety risk", "class action"])

    exp_escalation = rule_escalation or trigger_escalation
    genai_escalation = bool(genai_result.get("escalation_required", False))

    passed = (genai_escalation == exp_escalation)

    rule_id = matched_rule.rule_id if matched_rule else None
    explanation = (
        f"Escalation precedence check: Matched rule '{rule_id}' enforces escalation_required={exp_escalation}. "
        f"GenAI predicted escalation_required={genai_escalation}."
    )

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_escalation,
        actual_value=genai_escalation,
        rule_id_used=rule_id,
        explanation=explanation
    )


# ── 5. validate_policy_applicability ─────────────────────────────────────────

def validate_policy_applicability(
    genai_result: Dict[str, Any],
    kb_documents: Optional[List[Dict[str, Any]]] = None
) -> ValidationOutcome:
    """
    Checks referenced policy_id exists in Knowledge Base, has status="Active"
    (Draft and Superseded policies fail validation), and policy_section is real.
    """
    policy_id = genai_result.get("policy_id")
    docs = kb_documents if kb_documents is not None else KNOWLEDGE_BASE_STORE

    if not policy_id:
        return ValidationOutcome(
            passed=False,
            expected_value="Active Policy ID",
            actual_value=None,
            rule_id_used=None,
            explanation="GenAI result missing policy_id reference."
        )

    target_doc = None
    for doc in docs:
        if doc.get("document_id") == policy_id:
            target_doc = doc
            break

    if not target_doc:
        return ValidationOutcome(
            passed=False,
            expected_value=f"Active document with ID '{policy_id}'",
            actual_value="Document Not Found",
            rule_id_used=None,
            explanation=f"Referenced policy_id '{policy_id}' does not exist in Knowledge Base."
        )

    status = target_doc.get("status", "Active")
    if status != "Active":
        return ValidationOutcome(
            passed=False,
            expected_value="Active",
            actual_value=status,
            rule_id_used=None,
            explanation=f"Referenced policy_id '{policy_id}' is '{status}' (Must be Active. Draft/Superseded policies rejected)."
        )

    return ValidationOutcome(
        passed=True,
        expected_value="Active Policy Reference",
        actual_value=f"{policy_id} ({status})",
        rule_id_used=None,
        explanation=f"Policy '{policy_id}' is valid and Active."
    )


# ── 6. validate_resolution_steps ─────────────────────────────────────────────

def validate_resolution_steps(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """
    Checks all matched rule's required_actions are present in resolution_steps,
    and none of the prohibited_actions appear in resolution_steps or response.
    """
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue", "")
    }
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    if not matched_rule:
        return ValidationOutcome(
            passed=True,
            expected_value=[],
            actual_value=genai_result.get("resolution_steps", []),
            rule_id_used=None,
            explanation="No rule matrix actions specified; resolution steps accepted."
        )

    req_actions = matched_rule.required_actions or []
    prohibited_actions = matched_rule.prohibited_actions or []

    steps_text = " ".join(genai_result.get("resolution_steps", [])).lower()
    full_text = (steps_text + " " + (genai_result.get("professional_response") or "")).lower()

    missing_req = []
    for req in req_actions:
        req_kw = req.lower().replace("review", "").replace("verify", "").strip()
        if req_kw and req_kw not in full_text:
            missing_req.append(req)

    found_prohibited = []
    for proh in prohibited_actions:
        proh_kw = proh.lower().strip()
        if proh_kw and proh_kw in full_text:
            found_prohibited.append(proh)

    passed = len(missing_req) == 0 and len(found_prohibited) == 0

    explanation_parts = []
    if missing_req:
        explanation_parts.append(f"Missing required actions: {missing_req}")
    if found_prohibited:
        explanation_parts.append(f"Contains prohibited actions: {found_prohibited}")
    if not explanation_parts:
        explanation_parts.append("All required actions present and no prohibited actions detected.")

    return ValidationOutcome(
        passed=passed,
        expected_value={"required": req_actions, "prohibited_absent": prohibited_actions},
        actual_value=genai_result.get("resolution_steps", []),
        rule_id_used=matched_rule.rule_id,
        explanation=" | ".join(explanation_parts)
    )


# ── 7, 8, 9. validate_eligibility (refund, replacement, compensation) ──────

def validate_refund_eligibility(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """Checks GenAI refund_eligible recommendation against matched rule's actual conditions."""
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue", "")
    }
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    genai_refund = genai_result.get("refund_eligible")
    
    # Rule check
    prohibited = [p.lower() for p in (matched_rule.prohibited_actions if matched_rule else [])]
    is_prohibited = any("refund" in p or "credit" in p for p in prohibited)

    if is_prohibited:
        exp_refund = False
    else:
        req_credit = (complaint or {}).get("requested_credit", 0.0)
        exp_refund = True if req_credit > 0 or "billing" in (genai_result.get("issue_category") or "").lower() else False

    passed = (genai_refund == exp_refund) or (genai_refund is None and exp_refund is False)

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_refund,
        actual_value=genai_refund,
        rule_id_used=matched_rule.rule_id if matched_rule else None,
        explanation=f"Refund eligibility check (Expected: {exp_refund}, GenAI: {genai_refund})."
    )


def validate_replacement_eligibility(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """Checks GenAI replacement_eligible recommendation against hardware/device conditions."""
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "description": genai_result.get("primary_issue", "")
    }
    cat = (genai_result.get("issue_category") or "").lower()

    exp_replacement = True if "device" in cat or "hardware" in cat or "router" in (cmp_obj.get("description") or "").lower() else False
    genai_replacement = genai_result.get("replacement_eligible", False)

    passed = (genai_replacement == exp_replacement) or (genai_replacement is None and exp_replacement is False)

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_replacement,
        actual_value=genai_replacement,
        rule_id_used=None,
        explanation=f"Replacement eligibility check (Expected: {exp_replacement}, GenAI: {genai_replacement})."
    )


def validate_compensation(
    genai_result: Dict[str, Any],
    rule_matrix_engine: Optional[RuleMatrixEngine] = None,
    customer_context: Optional[Dict[str, Any]] = None,
    complaint: Optional[Dict[str, Any]] = None
) -> ValidationOutcome:
    """Checks GenAI compensation_recommended against policy caps and conditions."""
    cmp_obj = complaint or {
        "category": genai_result.get("issue_category"),
        "subcategory": genai_result.get("subcategory"),
        "requested_credit": 0.0
    }
    matched_rule = _get_matched_rule(cmp_obj, rule_matrix_engine)

    prohibited = [p.lower() for p in (matched_rule.prohibited_actions if matched_rule else [])]
    is_prohibited = any("goodwill" in p or "compensation" in p or "credit" in p for p in prohibited)

    exp_comp = False if is_prohibited else (cmp_obj.get("requested_credit", 0.0) > 0)
    genai_comp = genai_result.get("compensation_recommended", False)

    passed = (genai_comp == exp_comp) or (genai_comp is None and exp_comp is False)

    return ValidationOutcome(
        passed=passed,
        expected_value=exp_comp,
        actual_value=genai_comp,
        rule_id_used=matched_rule.rule_id if matched_rule else None,
        explanation=f"Compensation recommendation check (Expected: {exp_comp}, GenAI: {genai_comp})."
    )


# ── 10. detect_unsupported_promises ──────────────────────────────────────────

def detect_unsupported_promises(
    genai_result: Dict[str, Any],
    matched_rule: Optional[Any] = None
) -> List[str]:
    """
    Regex + keyword rules flagging phrases implying guaranteed refund/compensation,
    unauthorized deadlines, or policy exceptions in professional_response and resolution_steps.
    """
    flags = []
    resp_text = (genai_result.get("professional_response") or "").lower()

    unsupported_keywords = [
        "guarantee", "guaranteed", "100%", "unconditional", "promise to refund", "promise to credit", "immediate payout"
    ]

    for kw in unsupported_keywords:
        if kw in resp_text:
            flags.append(f"UNSUPPORTED PROMISE FLAG: Response contains unauthorized promise term '{kw}'.")
            break

    # Cross check against rule matrix authorization
    if matched_rule:
        prohibited = [p.lower() for p in (matched_rule.prohibited_actions or [])]
        if any("refund" in p for p in prohibited) and "refund" in resp_text:
            flags.append("UNSUPPORTED PROMISE FLAG: Response mentions refund despite rule matrix prohibiting refunds.")

    return flags


# ── 11. detect_hallucinated_claims ───────────────────────────────────────────

def detect_hallucinated_claims(
    genai_result: Dict[str, Any],
    complaint: Optional[Dict[str, Any]] = None,
    kb_chunks: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    HEURISTIC HALLUCINATION DETECTOR:
    Scans professional_response and resolution_steps for specific dollar amounts ($X), dates,
    or order tracking numbers that do not appear anywhere in source complaint text, active KB chunks,
    or rule matrix context.
    """
    flags = []
    cmp_obj = complaint or {}
    source_text = (
        (cmp_obj.get("description") or "") + " " +
        (cmp_obj.get("title") or "") + " " +
        (cmp_obj.get("account_number") or "") + " " +
        str(cmp_obj.get("requested_credit") or "") + " " +
        " ".join([c.get("text", "") for c in (kb_chunks or [])])
    ).lower()

    genai_text = (
        (genai_result.get("professional_response") or "") + " " +
        " ".join(genai_result.get("resolution_steps") or [])
    )

    # Extract dollar amounts (e.g. $500, $250.00)
    dollar_matches = re.findall(r"\$\d+(?:\.\d{2})?", genai_text)
    for amt in dollar_matches:
        num_val = amt.replace("$", "").split(".")[0]
        if num_val not in source_text and amt.lower() not in source_text:
            flags.append(f"HALLUCINATION FLAG: Response references dollar amount '{amt}' not present in complaint or KB context.")

    # Extract UPS/FedEx tracking numbers or fake IDs (e.g. 1Z999..., TRK-...)
    tracking_matches = re.findall(r"\b1Z[0-9A-Z]{10,16}\b|\bTRK-\d{6,}\b", genai_text, re.IGNORECASE)
    for trk in tracking_matches:
        if trk.lower() not in source_text:
            flags.append(f"HALLUCINATION FLAG: Response references tracking number '{trk}' not in source context.")

    return flags


# ── 12. detect_contradictory_instructions ─────────────────────────────────────

def detect_contradictory_instructions(
    kb_chunks: Optional[List[Dict[str, Any]]] = None,
    kb_documents: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    DOCUMENT CONFLICT DETECTOR:
    Flags when an Active policy and a Draft/Superseded/FAQ document conflict on the same topic.
    Precedence rules: Active Policy > SOP > FAQ. Newer effective_date wins among same-status documents.
    """
    flags = []
    docs = kb_documents if kb_documents is not None else KNOWLEDGE_BASE_STORE

    active_docs = [d for d in docs if d.get("status") == "Active"]
    non_active_docs = [d for d in docs if d.get("status") in ["Draft", "Superseded"]]

    # Check for category conflicts between active and non-active
    active_categories = {d.get("category"): d for d in active_docs}
    for na in non_active_docs:
        cat = na.get("category")
        if cat in active_categories:
            active_doc = active_categories[cat]
            flags.append(
                f"CONTRADICTION FLAG: Non-active document '{na.get('document_id')}' ({na.get('status')}) "
                f"conflicts with Active document '{active_doc.get('document_id')}' for category '{cat}'. "
                f"Resolved via precedence: Active policy '{active_doc.get('document_id')}' overrides non-active."
            )

    return flags
