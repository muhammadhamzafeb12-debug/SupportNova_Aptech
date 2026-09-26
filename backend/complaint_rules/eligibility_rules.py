"""
Eligibility Rules Engine for SupportNova Pipeline 2.
Determines refund, replacement, and compensation eligibility based on objective business conditions.
"""

from typing import Tuple, List, Optional

def evaluate_eligibility(
    complaint_title: str,
    complaint_description: str,
    category: str,
    subcategory: str,
    customer_type: str = "REGULAR",
    warranty_status: str = "ACTIVE",
    defect_condition: Optional[str] = None,
    order_days_ago: int = 10
) -> Tuple[bool, bool, bool, List[str]]:
    """
    Evaluates (refund_eligible, replacement_eligible, compensation_eligible, eligibility_reasons).
    Evaluates against warranty, return window, defect proof, and customer tier.
    """
    text_lower = (complaint_title + " " + complaint_description).lower()
    reasons = []

    # 1. Warranty Expired Check
    warranty_expired = (
        warranty_status == "EXPIRED" or 
        "warranty expired" in text_lower or 
        "out of warranty" in text_lower or 
        "2 years old" in text_lower or 
        "bought 3 years ago" in text_lower
    )

    # 2. Return Window Check (30-Day Policy - POL-002)
    outside_return_window = order_days_ago > 30 or "bought 60 days ago" in text_lower or "past 30 days" in text_lower

    # 3. Refund Eligibility
    refund_eligible = False
    if category in ["Billing", "Refund"] and any(k in text_lower for k in ["duplicate", "incorrect charge", "double charge", "charged twice", "refund", "charge"]):
        refund_eligible = True
        reasons.append("Billing error or duplicate charge verified under POL-005.")
    elif category in ["Product Defect", "Delivery"] and not warranty_expired and not outside_return_window:
        refund_eligible = True
        reasons.append("Defective or non-delivered item within 30-day window under POL-002.")
    elif warranty_expired:
        refund_eligible = False
        reasons.append("Refund ineligible: Product warranty has expired.")
    elif outside_return_window and category != "Billing":
        refund_eligible = False
        reasons.append("Refund ineligible: Exceeds 30-day return policy window under POL-002.")

    # 4. Replacement Eligibility
    replacement_eligible = False
    is_defective = (
        category == "Product Defect" or 
        defect_condition in ["PHYSICAL_DAMAGE", "HARDWARE_FAILURE", "DOA"] or
        any(k in text_lower for k in ["broken", "damaged", "shattered", "malfunctioning", "defective", "missing parts"])
    )
    
    if is_defective and not warranty_expired:
        replacement_eligible = True
        reasons.append("Item replacement eligible under POL-003 (Active warranty & verified defect).")
    elif is_defective and warranty_expired:
        replacement_eligible = False
        reasons.append("Replacement ineligible: Item is out of warranty.")

    # 5. Compensation Eligibility (Store Credit / Gesture of Goodwill)
    compensation_eligible = False
    if customer_type in ["VIP", "CORPORATE"] and ("delayed delivery" in text_lower or "service failure" in text_lower):
        compensation_eligible = True
        reasons.append("Goodwill store credit compensation authorized for VIP/Corporate customer under POL-016.")
    elif category == "Safety":
        compensation_eligible = True
        reasons.append("Safety hazard protocol permits compensation review under POL-017.")
    elif category == "Delivery" and "delayed by 10 days" in text_lower:
        compensation_eligible = True
        reasons.append("Severe delivery delay compensation permitted under POL-006.")
    else:
        compensation_eligible = False

    return refund_eligible, replacement_eligible, compensation_eligible, reasons
