"""
Pydantic Schema and Custom Exceptions for Pipeline 1 GenAI Complaint Analysis.
Validates structured JSON output against NexaLink configuration categories and departments.
"""
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from backend.config_loader import load_categories_config, load_departments_config

logger = logging.getLogger(__name__)

# Load valid category and department tokens from configuration files
CATEGORIES_CFG = load_categories_config()
DEPARTMENTS_CFG = load_departments_config()


def _get_valid_category_names() -> set:
    names = set()
    for cat in CATEGORIES_CFG.get("categories", []):
        if "name" in cat:
            names.add(cat["name"].strip().lower())
        if "code" in cat:
            names.add(cat["code"].strip().lower())
    return names


def _get_valid_subcategory_names() -> set:
    names = set()
    for cat in CATEGORIES_CFG.get("categories", []):
        for sub in cat.get("subcategories", []):
            if "name" in sub:
                names.add(sub["name"].strip().lower())
            if "code" in sub:
                names.add(sub["code"].strip().lower())
    return names


def _get_valid_department_names() -> set:
    names = set()
    for dept in DEPARTMENTS_CFG.get("departments", []):
        for k in ("name", "short_name", "code", "id"):
            if k in dept and dept[k]:
                names.add(str(dept[k]).strip().lower())
    return names


VALID_CATEGORIES = _get_valid_category_names()
VALID_SUBCATEGORIES = _get_valid_subcategory_names()
VALID_DEPARTMENTS = _get_valid_department_names()


class SchemaValidationError(ValueError):
    """Custom exception raised when GenAI output violates JSON schema constraints."""
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []


class ComplaintAnalysisResult(BaseModel):
    complaint_id: str
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    issue_category: str
    subcategory: str
    sentiment: Literal["Positive", "Neutral", "Negative", "Strongly Negative"]
    urgency: Literal["Low", "Medium", "High", "Critical"]
    priority: Literal["P3", "P2", "P1", "P0"]
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    department: str
    supporting_departments: List[str] = Field(default_factory=list)
    policy_id: Optional[str] = None
    policy_section: Optional[str] = None
    resolution_steps: List[str] = Field(default_factory=list)
    refund_eligible: Optional[bool] = None
    replacement_eligible: Optional[bool] = None
    compensation_recommended: Optional[bool] = None
    escalation_required: bool = False
    escalation_level: Optional[str] = None
    escalation_reason: Optional[str] = None
    professional_response: str
    follow_up_required: bool = False
    follow_up_message: Optional[str] = None
    clarification_questions: List[str] = Field(default_factory=list)
    complaint_summary: str
    agent_guidance: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    priority_urgency_mismatch: Optional[str] = None

    @field_validator("issue_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if not v or v.strip().lower() not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Must be one of config/categories.json values.")
        return v

    @field_validator("subcategory")
    @classmethod
    def validate_subcategory(cls, v: str) -> str:
        if not v or v.strip().lower() not in VALID_SUBCATEGORIES:
            raise ValueError(f"Invalid subcategory '{v}'. Must be one of config/categories.json values.")
        return v

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        if not v or v.strip().lower() not in VALID_DEPARTMENTS:
            raise ValueError(f"Invalid department '{v}'. Must be one of config/departments.json values.")
        return v

    @field_validator("supporting_departments")
    @classmethod
    def validate_supporting_departments(cls, v_list: List[str]) -> List[str]:
        for dept in v_list:
            if dept and dept.strip().lower() not in VALID_DEPARTMENTS:
                raise ValueError(f"Invalid supporting department '{dept}'. Must be one of config/departments.json values.")
        return v_list

    @model_validator(mode="after")
    def check_priority_urgency_alignment(self):
        """
        Validates priority against urgency mapping.
        Critical->P0, High->P1, Medium->P2, Low->P3.
        Flags a warning if mismatched without auto-correcting (Pipeline 2 makes final call).
        """
        expected_mapping = {
            "Critical": "P0",
            "High": "P1",
            "Medium": "P2",
            "Low": "P3"
        }
        expected_prio = expected_mapping.get(self.urgency)
        if expected_prio and self.priority != expected_prio:
            warning_msg = (
                f"Priority warning: Urgency '{self.urgency}' expects priority '{expected_prio}', "
                f"but GenAI assigned '{self.priority}'."
            )
            logger.warning(warning_msg)
            self.priority_urgency_mismatch = warning_msg

        return self
