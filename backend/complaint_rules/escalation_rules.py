"""
Escalation Rules Engine for SupportNova Pipeline 2.
Evaluates complaints deterministically against safety, security, legal, repeat, and value triggers.
"""

from typing import Tuple, Optional
from backend.models import EscalationLevel

def evaluate_escalation(
    complaint_title: str,
    complaint_description: str,
    category: str,
    customer_type: str = "REGULAR",
    prev_complaint_ref: Optional[str] = None,
    order_amount: Optional[float] = None
) -> Tuple[bool, str, str, str, str]:
    """
    Evaluates escalation requirement, escalation level, escalation reason, urgency, and priority.
    Returns (escalation_required, escalation_level, escalation_reason, verified_urgency, verified_priority).
    Distinguishes customer tone from objective business risk.
    """
    text_lower = (complaint_title + " " + complaint_description).lower()

    # 1. Safety Hazard - Emergency Escalation (SRS requirement #23 & #33)
    safety_keywords = ["fire", "hazard", "burn", "electric shock", "injury", "poison", "explode", "smoke", "sparks", "hospital", "bleeding"]
    if category == "Safety" or any(kw in text_lower for kw in safety_keywords):
        return (
            True,
            EscalationLevel.CRITICAL_MANAGEMENT.value,
            "Mandatory emergency safety hazard escalation (POL-017).",
            "Critical",
            "P0 – Critical"
        )

    # 2. Privacy & Data Security Breach
    privacy_keywords = ["data breach", "privacy leak", "stolen password", "hacked", "gdpr", "unauthorized access", "identity theft"]
    if category == "Privacy" or any(kw in text_lower for kw in privacy_keywords):
        return (
            True,
            EscalationLevel.COMPLIANCE.value,
            "Mandatory data privacy & security compliance escalation (POL-008).",
            "High",
            "P1 – High"
        )

    # 3. Legal Threat
    legal_keywords = ["attorney", "lawyer", "lawsuit", "suing", "legal action", "court", "subpoena", "regulatory complaint"]
    if any(kw in text_lower for kw in legal_keywords):
        return (
            True,
            EscalationLevel.COMPLIANCE.value,
            "Customer indicated potential legal action. Compliance & legal review required.",
            "High",
            "P1 – High"
        )

    # 4. Repeated Unresolved Complaint
    if prev_complaint_ref or "second time" in text_lower or "repeat ticket" in text_lower or "unresolved for 2 weeks" in text_lower:
        return (
            True,
            EscalationLevel.SUPERVISOR.value,
            f"Repeat unresolved complaint (Ref: {prev_complaint_ref or 'Previous Ticket'}) flagged for supervisor review.",
            "High",
            "P1 – High"
        )

    # 5. High-Value Dispute (>$500 or Corporate VIP)
    if (order_amount and order_amount > 500) or (customer_type in ["VIP", "CORPORATE"] and "dispute" in text_lower):
        return (
            True,
            EscalationLevel.DEPARTMENT_MANAGER.value,
            f"High-value dispute or corporate VIP account escalation ($500+ or {customer_type}).",
            "High",
            "P1 – High"
        )

    # 6. Severe Service Failure
    if "system failure" in text_lower or "outage" in text_lower or "fraud" in text_lower:
        return (
            True,
            EscalationLevel.SPECIALIST_TEAM.value,
            "Severe operational service failure detected.",
            "High",
            "P1 – High"
        )

    # 7. Default handling (Angry tone vs objective low risk)
    # If customer is shouting ("angry", "unacceptable!!!", "worst service ever"), but issue is minor:
    angry_keywords = ["unacceptable", "furious", "terrible", "worst", "screaming", "angry", "ridiculous"]
    if any(kw in text_lower for kw in angry_keywords):
        # Tone is angry, but objective risk remains Medium/Low
        return (
            False,
            EscalationLevel.NONE.value,
            "Customer tone is angry, but issue remains standard SOP without mandatory escalation.",
            "Medium",
            "P2 – Medium"
        )

    # Standard calm customer
    return (
        False,
        EscalationLevel.NONE.value,
        "Standard complaint within operational SLA bounds.",
        "Low",
        "P3 – Low"
    )
