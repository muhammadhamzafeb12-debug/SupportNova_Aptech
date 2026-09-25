"""
Schema Pre-Check Module for Pipeline 2 — Python Ground-Truth Validation.
Validates GenAI response against Pydantic schema constraints, enum values,
and cross-checks category and department tokens against configuration JSON files.

Runs BEFORE business-rule validation. If this fails, Pipeline 2 halts with
pipeline2_status = "schema_invalid" and routes to Manual Review.
"""
from typing import Dict, Any, List, Tuple
from backend.schemas.complaint_analysis import ComplaintAnalysisResult, SchemaValidationError


def pre_check_schema(genai_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Re-validates GenAI result against Pydantic schema, enum constraints,
    and category/department definitions.
    
    Returns:
        (is_valid: bool, errors: List[str])
    """
    if not isinstance(genai_result, dict):
        return False, ["GenAI result is not a valid JSON dictionary."]

    errors = []

    # Required field presence check
    required_fields = [
        "complaint_id", "primary_issue", "issue_category", "subcategory",
        "sentiment", "urgency", "priority", "department", "professional_response",
        "complaint_summary"
    ]
    for field in required_fields:
        if field not in genai_result or genai_result[field] is None or genai_result[field] == "":
            errors.append(f"Missing required schema field '{field}'.")

    if errors:
        return False, errors

    # Full Pydantic validation (enums, categories, departments)
    try:
        ComplaintAnalysisResult(**genai_result)
        return True, []
    except Exception as exc:
        err_msg = str(exc)
        # Extract readable error details
        formatted_errs = [f"Schema pre-check error: {line.strip()}" for line in err_msg.splitlines() if "Value error" in line or "Input should be" in line or "type_error" in line or "Field required" in line]
        if not formatted_errs:
            formatted_errs = [f"Schema pre-check validation failed: {err_msg}"]
        return False, formatted_errs
