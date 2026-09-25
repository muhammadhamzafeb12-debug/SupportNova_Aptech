"""
Pydantic Schemas for SupportNova FastAPI API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from backend.schemas.complaint_analysis import ComplaintAnalysisResult, SchemaValidationError

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Optional[str] = "Customer"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    created_at: Optional[datetime] = None

# Complaint Schemas
class ComplaintCreate(BaseModel):
    customer_email: EmailStr
    customer_name: str
    account_number: Optional[str] = ""
    title: str
    category: str
    sub_category: Optional[str] = ""
    description: str
    requested_credit: Optional[float] = 0.0

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_department: Optional[str] = None
    assigned_agent: Optional[str] = None
    resolution_notes: Optional[str] = None
    approved_credit: Optional[float] = None

class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    customer_email: str
    customer_name: str
    account_number: Optional[str] = ""
    title: str
    category: str
    sub_category: Optional[str] = ""
    description: str
    status: str
    priority: str
    assigned_department: Optional[str] = ""
    assigned_agent: Optional[str] = ""
    sentiment_score: Optional[float] = 0.5
    genai_summary: Optional[str] = ""
    genai_suggested_response: Optional[str] = ""
    genai_confidence: Optional[float] = 0.85
    python_validation_passed: Optional[bool] = True
    python_validation_flags: Optional[List[str]] = []
    has_hallucination: Optional[bool] = False
    hallucination_details: Optional[str] = ""
    requested_credit: Optional[float] = 0.0
    approved_credit: Optional[float] = 0.0
    resolution_notes: Optional[str] = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Knowledge Base Schemas
class KBDocumentCreate(BaseModel):
    title: str
    category: str
    document_type: str = "policy"
    content: str
    tags: Optional[str] = ""

class KBDocumentResponse(BaseModel):
    id: int
    document_id: Optional[str] = None
    title: str
    category: str
    version: Optional[str] = "1.0"
    status: Optional[str] = "Active"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: Optional[Any] = None

    class Config:
        from_attributes = True

class KBUploadErrorResponse(BaseModel):
    error_code: str
    detail: str
    message: str

class ActivateDocumentRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Required confirmation reason for activating draft policy")

class KBVersionAuditResponse(BaseModel):
    id: int
    document_id: str
    title: str
    category: str
    previous_status: Optional[str] = None
    new_status: str
    previous_version: Optional[str] = None
    new_version: str
    changed_at: str
    changed_by: str
    reason: Optional[str] = None


# Rule Matrix Schemas
class RuleMatrixItem(BaseModel):
    rule_id: str
    category: str
    subcategory: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    department: str
    supporting_departments: Optional[List[str]] = []
    urgency: str = "Medium"
    priority: str = "Medium"
    policy_id: str
    escalation_required: bool = False
    escalation_level: Optional[str] = None
    required_actions: List[str] = []
    prohibited_actions: List[str] = []
    follow_up_required: bool = False
    is_active: bool = True
    created_by: Optional[str] = "admin@nexalink.com"
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    class Config:
        from_attributes = True

class RuleMatrixCreate(BaseModel):
    rule_id: Optional[str] = None
    category: str
    subcategory: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    department: str
    supporting_departments: Optional[List[str]] = []
    urgency: str = "Medium"
    priority: str = "Medium"
    policy_id: str
    escalation_required: bool = False
    escalation_level: Optional[str] = None
    required_actions: List[str] = []
    prohibited_actions: List[str] = []
    follow_up_required: bool = False

class RuleMatrixUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    department: Optional[str] = None
    supporting_departments: Optional[List[str]] = None
    urgency: Optional[str] = None
    priority: Optional[str] = None
    policy_id: Optional[str] = None
    escalation_required: Optional[bool] = None
    escalation_level: Optional[str] = None
    required_actions: Optional[List[str]] = None
    prohibited_actions: Optional[List[str]] = None
    follow_up_required: Optional[bool] = None
    is_active: Optional[bool] = None

class RuleMatrixAuditResponse(BaseModel):
    id: int
    rule_id: str
    action: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    changed_by: str
    changed_at: Any


# Validation & Pipeline Schemas
class PipelineTriggerRequest(BaseModel):
    complaint_id: int
    force_reprocess: Optional[bool] = False

class ValidationResult(BaseModel):
    complaint_id: int
    passed: bool
    flags: List[str]
    suggested_department: str
    recommended_credit: float
    regulatory_warning: bool

class ComparisonResult(BaseModel):
    complaint_id: int
    genai_category: str
    python_category: str
    category_matches: bool
    genai_credit: float
    python_credit_limit: float
    credit_override_flag: bool
    hallucination_detected: bool
    hallucination_reason: Optional[str] = None
    review_required: bool

# Dashboard Schemas
class DashboardSummary(BaseModel):
    role: str
    metrics: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
