"""
Pipeline 2 Entrypoint: Independent Python Ground-Truth Validation Engine.
Delegates to backend.complaint_rules.ground_truth_validator for deterministic validation.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.schemas.schemas import GenAIResponseSchema, PythonValidationSchema
from backend.complaint_rules.ground_truth_validator import run_ground_truth_validation

def evaluate_ground_truth(
    db: Session,
    complaint_title: str,
    complaint_description: str,
    genai_output: GenAIResponseSchema,
    customer_type: str = "REGULAR",
    prev_complaint_ref: Optional[str] = None,
    warranty_status: str = "ACTIVE",
    defect_condition: Optional[str] = None
) -> PythonValidationSchema:
    """
    Pipeline 2: Independent Python Ground-Truth Validation Engine.
    Executes deterministic Python business logic without relying on any LLM.
    """
    return run_ground_truth_validation(
        db=db,
        complaint_title=complaint_title,
        complaint_description=complaint_description,
        genai_output=genai_output,
        customer_type=customer_type,
        prev_complaint_ref=prev_complaint_ref,
        warranty_status=warranty_status,
        defect_condition=defect_condition,
        complaint_id_str=genai_output.complaint_id if genai_output else "CMP-TEMP"
    )
