from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    full_name: str
    email: str
    is_active: bool

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username_or_email: str
    password: str
    remember_me: Optional[bool] = False

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "CUSTOMER"
    department_id: Optional[int] = None

class UserUpdateRole(BaseModel):
    role: str

class UserUpdateStatus(BaseModel):
    is_active: bool

class ForgotPasswordRequest(BaseModel):
    email_or_username: str

class ResetPasswordRequest(BaseModel):
    token_or_username: str
    new_password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Complaint Submission & Schema
class ComplaintCreate(BaseModel):
    title: str
    description: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_type: Optional[str] = "REGULAR"
    product_service: Optional[str] = None
    order_ref: Optional[str] = None
    transaction_ref: Optional[str] = None
    prev_complaint_ref: Optional[str] = None
    channel: Optional[str] = "WEB_FORM"
    preferred_contact: Optional[str] = "EMAIL"

class ComplaintOut(BaseModel):
    id: int
    complaint_code: str
    title: str
    description: str
    customer_type: str
    product_service: Optional[str] = None
    order_ref: Optional[str] = None
    transaction_ref: Optional[str] = None
    prev_complaint_ref: Optional[str] = None
    channel: str
    preferred_contact: str
    submitted_at: datetime
    status: str
    assigned_agent_id: Optional[int] = None
    department_id: Optional[int] = None
    priority: str
    urgency: str
    sentiment: str
    is_duplicate: bool
    duplicate_of_code: Optional[str] = None
    prompt_injection_flag: bool

    class Config:
        from_attributes = True

# Structured JSON response expected from GenAI Pipeline (as per SRS requirement #18)
class GenAIResponseSchema(BaseModel):
    complaint_id: str
    primary_issue: str
    secondary_issues: List[str] = []
    category: str
    subcategory: str
    sentiment: str
    urgency: str
    priority: str
    entities: Dict[str, Any] = {}
    department: str
    supporting_departments: List[str] = []
    policy_references: List[Dict[str, Any]] = []
    resolution_steps: List[str] = []
    escalation_required: bool = False
    escalation_level: str = "No Escalation"
    escalation_reason: str = ""
    customer_response: str = ""
    follow_up_required: bool = False
    follow_up_message: str = ""
    clarification_questions: List[str] = []
    agent_guidance: List[str] = []

# Python Validation Output Schema
class PythonValidationSchema(BaseModel):
    complaint_id: str
    rule_id_matched: Optional[str] = None
    verified_category: str
    verified_subcategory: str
    verified_department: str
    supporting_departments: List[str] = []
    verified_urgency: str
    verified_priority: str
    verified_escalation_required: bool
    verified_escalation_level: str
    verified_escalation_reason: str
    verified_refund_eligible: bool
    verified_replacement_eligible: bool
    verified_compensation_eligible: bool
    verified_sla_hours: int = 24
    verified_policy_id: Optional[str] = None
    verified_policy_section: Optional[str] = None
    mandatory_actions: List[str] = []
    prohibited_actions: List[str] = []
    policy_grounding_valid: bool = True
    unsupported_claims: List[str] = []
    contradictions: List[str] = []
    missing_actions: List[str] = []

# Comparison Output Schema
class MismatchDetail(BaseModel):
    field: str
    genai_val: Any
    expected_val: Any
    reason: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW

class ComparisonOut(BaseModel):
    id: int
    complaint_id: int
    overall_status: str
    schema_compliance_score: float
    policy_compliance_score: float
    routing_compliance_score: float
    urgency_compliance_score: float
    escalation_compliance_score: float
    resolution_compliance_score: float
    source_traceability_score: float
    overall_verification_score: float
    mismatches: List[MismatchDetail] = []

# Standalone Pipeline 2 Validation Request
class StandaloneValidationRequest(BaseModel):
    complaint_title: str
    complaint_description: str
    genai_output: Optional[GenAIResponseSchema] = None
    customer_type: Optional[str] = "REGULAR"
    prev_complaint_ref: Optional[str] = None
    product_service: Optional[str] = None
    order_ref: Optional[str] = None
    warranty_status: Optional[str] = "ACTIVE"
    defect_condition: Optional[str] = None

# Reviewer Action Schema
class ReviewActionCreate(BaseModel):
    reviewer_action: str # APPROVE, REJECT, MODIFY, RECLASSIFY, REASSIGN, ESCALATE
    modified_category: Optional[str] = None
    modified_department: Optional[str] = None
    modified_escalation_level: Optional[str] = None
    reviewer_comments: Optional[str] = None

# Document / Policy Create Schema
class PolicyCreate(BaseModel):
    doc_id: str
    title: str
    category: str
    status: str = "ACTIVE"
    version: str = "1.0"
    effective_date: Optional[str] = "2026-01-01"
    expiry_date: Optional[str] = "2027-12-31"
    content: str
    source_reference: str = "NovaCart Standard Policy"

# Rule Matrix Entry Schema
class RuleMatrixEntry(BaseModel):
    rule_id: str
    category: str
    subcategory: str
    conditions: str
    department: str
    urgency: str
    priority: str
    policy_doc_id: Optional[str] = None
    policy_section: Optional[str] = "SECTION 2"
    escalation_required: bool = False
    escalation_level: str = "No Escalation"
    required_actions: List[str] = []
    prohibited_actions: List[str] = []
    refund_eligible: bool = False
    replacement_eligible: bool = False
    compensation_eligible: bool = False
    follow_up_required: bool = False
    sla_hours: int = 24
    rule_priority: int = 1
    is_active: bool = True
    version: str = "1.0"

# Prompt Template Schema
class PromptTemplateSchema(BaseModel):
    prompt_code: str
    name: str
    provider: str = "all"
    model: str = "all"
    version: str = "1.0"
    template_text: str
    system_instruction: str
    status: str = "ACTIVE"

# --- SKILLSPRINT AI SCHEMAS ---

class EmployeeProfileCreate(BaseModel):
    employee_code: Optional[str] = None
    full_name: str
    email: str
    department: str
    role_title: str
    seniority_level: Optional[str] = "Junior"
    prior_experience_years: Optional[float] = 0.0
    current_skills: Optional[List[str]] = []

class EmployeeProfileOut(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: str
    department: str
    role_title: str
    seniority_level: str
    prior_experience_years: float
    current_skills: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class RoleRequirementMatrixCreate(BaseModel):
    role_code: str
    role_title: str
    department: str
    required_skills: List[str] = []
    required_sops: List[str] = []
    core_competencies: List[str] = []
    minimum_passing_quiz_score: Optional[int] = 80
    onboarding_duration_days: Optional[int] = 14

class RoleRequirementMatrixOut(BaseModel):
    id: int
    role_code: str
    role_title: str
    department: str
    required_skills: List[str] = []
    required_sops: List[str] = []
    core_competencies: List[str] = []
    minimum_passing_quiz_score: int
    onboarding_duration_days: int

    class Config:
        from_attributes = True

class OnboardingGenerateRequest(BaseModel):
    employee_id: int
    role_code: str

class OnboardingPlanOut(BaseModel):
    id: int
    plan_code: str
    employee_id: int
    role_title: str
    status: str
    learning_modules: List[Dict[str, Any]] = []
    checklists: List[Dict[str, Any]] = []
    tasks: List[Dict[str, Any]] = []
    quizzes: List[Dict[str, Any]] = []
    assessments: List[Dict[str, Any]] = []
    coverage_score: float
    traceability_score: float
    consistency_score: float
    verification_status: str
    contradictions_detected: List[str] = []
    missing_requirements: List[str] = []
    verified_sources: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

