import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"
    REVIEWER = "REVIEWER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

class ComplaintStatus(str, enum.Enum):
    NEW = "NEW"
    ANALYZED = "ANALYZED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_CUSTOMER = "AWAITING_CUSTOMER"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"

class PolicyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DRAFT = "DRAFT"
    OUTDATED = "OUTDATED"

class UrgencyLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class PriorityLevel(str, enum.Enum):
    P3 = "P3 – Low"
    P2 = "P2 – Medium"
    P1 = "P1 – High"
    P0 = "P0 – Critical"

class EscalationLevel(str, enum.Enum):
    NONE = "No Escalation"
    SUPERVISOR = "Supervisor Review"
    DEPARTMENT_MANAGER = "Department Manager"
    SPECIALIST_TEAM = "Specialist Team"
    COMPLIANCE = "Compliance Review"
    CRITICAL_MANAGEMENT = "Critical Management Escalation"

class ComparisonStatus(str, enum.Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    WARNING = "WARNING"
    REVIEW_REQUIRED = "REVIEW REQUIRED"

# --- DB MODELS ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.CUSTOMER.value, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_login = Column(DateTime, nullable=True)

    department = relationship("Department", back_populates="users")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    customer_type = Column(String(50), default="REGULAR") # REGULAR, PREMIUM, VIP, CORPORATE
    risk_profile = Column(String(50), default="LOW")
    account_created_at = Column(DateTime, default=utc_now)

    complaints = relationship("Complaint", back_populates="customer")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sla_hours_default = Column(Integer, default=24)

    users = relationship("User", back_populates="department")
    complaints = relationship("Complaint", back_populates="department")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    subcategories = relationship("Subcategory", back_populates="category")

class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    category = relationship("Category", back_populates="subcategories")

class RuleMatrix(Base):
    __tablename__ = "rule_matrix"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=False)
    conditions = Column(Text, nullable=False) # JSON or descriptive expression
    department = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    policy_doc_id = Column(String(100), nullable=True)
    policy_section = Column(String(100), nullable=True)
    escalation_required = Column(Boolean, default=False)
    escalation_level = Column(String(100), default=EscalationLevel.NONE.value)
    required_actions = Column(JSON, default=list)
    prohibited_actions = Column(JSON, default=list)
    refund_eligible = Column(Boolean, default=False)
    replacement_eligible = Column(Boolean, default=False)
    compensation_eligible = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    sla_hours = Column(Integer, default=24)
    rule_priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    version = Column(String(50), default="1.0")

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(String(50), default=PolicyStatus.ACTIVE.value)
    version = Column(String(50), default="1.0")
    effective_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(20), default="TXT")
    source_reference = Column(String(255), default="Internal SOP")
    created_at = Column(DateTime, default=utc_now)

    chunks = relationship("DocumentChunk", back_populates="policy", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    doc_id = Column(String(100), nullable=False)
    section_id = Column(String(100), nullable=True)
    heading = Column(String(255), nullable=True)
    page_number = Column(Integer, default=1)
    version = Column(String(50), default="1.0")
    content = Column(Text, nullable=False)

    policy = relationship("Policy", back_populates="chunks")

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_type = Column(String(50), default="REGULAR")
    product_service = Column(String(255), nullable=True)
    order_ref = Column(String(100), nullable=True)
    transaction_ref = Column(String(100), nullable=True)
    prev_complaint_ref = Column(String(100), nullable=True)
    channel = Column(String(50), default="WEB_FORM")
    preferred_contact = Column(String(50), default="EMAIL")
    submitted_at = Column(DateTime, default=utc_now)
    
    status = Column(String(50), default=ComplaintStatus.NEW.value)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    priority = Column(String(50), default=PriorityLevel.P3.value)
    urgency = Column(String(50), default=UrgencyLevel.LOW.value)
    sentiment = Column(String(50), default="Neutral")
    
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_code = Column(String(50), nullable=True)
    prompt_injection_flag = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])

    genai_analysis = relationship("GenAIAnalysis", back_populates="complaint", uselist=False)
    python_validation = relationship("PythonValidation", back_populates="complaint", uselist=False)
    comparison = relationship("Comparison", back_populates="complaint", uselist=False)
    manual_reviews = relationship("ManualReview", back_populates="complaint")
    sla_record = relationship("SLARecord", back_populates="complaint", uselist=False)

class GenAIAnalysis(Base):
    __tablename__ = "genai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_version = Column(String(50), default="1.0")
    
    primary_issue = Column(Text, nullable=True)
    secondary_issues = Column(JSON, default=list)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    sentiment = Column(String(50), nullable=True)
    urgency = Column(String(50), nullable=True)
    priority = Column(String(50), nullable=True)
    entities = Column(JSON, default=dict)
    department = Column(String(100), nullable=True)
    supporting_departments = Column(JSON, default=list)
    policy_references = Column(JSON, default=list)
    resolution_steps = Column(JSON, default=list)
    escalation_required = Column(Boolean, default=False)
    escalation_level = Column(String(100), default=EscalationLevel.NONE.value)
    escalation_reason = Column(Text, nullable=True)
    customer_response = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_message = Column(Text, nullable=True)
    clarification_questions = Column(JSON, default=list)
    agent_guidance = Column(JSON, default=list)
    
    raw_json_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    complaint = relationship("Complaint", back_populates="genai_analysis")

class PythonValidation(Base):
    __tablename__ = "python_validations"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    rule_id_matched = Column(String(50), nullable=True)
    
    verified_category = Column(String(100), nullable=True)
    verified_subcategory = Column(String(100), nullable=True)
    verified_department = Column(String(100), nullable=True)
    supporting_departments = Column(JSON, default=list)
    verified_urgency = Column(String(50), nullable=True)
    verified_priority = Column(String(50), nullable=True)
    
    verified_escalation_required = Column(Boolean, default=False)
    verified_escalation_level = Column(String(100), default=EscalationLevel.NONE.value)
    verified_escalation_reason = Column(Text, nullable=True)
    
    verified_refund_eligible = Column(Boolean, default=False)
    verified_replacement_eligible = Column(Boolean, default=False)
    verified_compensation_eligible = Column(Boolean, default=False)
    verified_sla_hours = Column(Integer, default=24)
    verified_policy_id = Column(String(100), nullable=True)
    verified_policy_section = Column(String(100), nullable=True)
    
    mandatory_actions = Column(JSON, default=list)
    prohibited_actions = Column(JSON, default=list)
    policy_grounding_valid = Column(Boolean, default=True)
    unsupported_claims = Column(JSON, default=list)
    contradictions = Column(JSON, default=list)
    missing_actions = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=utc_now)

    complaint = relationship("Complaint", back_populates="python_validation")

class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    overall_status = Column(String(50), default=ComparisonStatus.MATCH.value)
    
    schema_compliance_score = Column(Float, default=100.0)
    policy_compliance_score = Column(Float, default=100.0)
    routing_compliance_score = Column(Float, default=100.0)
    urgency_compliance_score = Column(Float, default=100.0)
    escalation_compliance_score = Column(Float, default=100.0)
    resolution_compliance_score = Column(Float, default=100.0)
    source_traceability_score = Column(Float, default=100.0)
    overall_verification_score = Column(Float, default=100.0)
    
    mismatches = Column(JSON, default=list) # [{field, genai_val, expected_val, reason, severity}]
    created_at = Column(DateTime, default=utc_now)

    complaint = relationship("Complaint", back_populates="comparison")

class ManualReview(Base):
    __tablename__ = "manual_reviews"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_reason = Column(Text, nullable=False)
    reviewer_action = Column(String(50), nullable=False) # APPROVE, REJECT, MODIFY, RECLASSIFY, REASSIGN, ESCALATE
    modified_category = Column(String(100), nullable=True)
    modified_department = Column(String(100), nullable=True)
    modified_escalation_level = Column(String(100), nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=utc_now)

    complaint = relationship("Complaint", back_populates="manual_reviews")

class SLARecord(Base):
    __tablename__ = "sla_records"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    response_deadline = Column(DateTime, nullable=False)
    resolution_deadline = Column(DateTime, nullable=False)
    response_met_at = Column(DateTime, nullable=True)
    resolution_met_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="ON_TRACK") # ON_TRACK, AT_RISK, BREACHED

    complaint = relationship("Complaint", back_populates="sla_record")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    prompt_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), default="all")
    model = Column(String(100), default="all")
    version = Column(String(50), default="1.0")
    template_text = Column(Text, nullable=False)
    system_instruction = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    complaint_code = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utc_now)

# --- SKILLSPRINT AI MODELS ---

class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    role_title = Column(String(100), nullable=False)
    seniority_level = Column(String(50), default="Junior") # Junior, Mid, Senior, Lead
    prior_experience_years = Column(Float, default=0.0)
    current_skills = Column(JSON, default=list) # ["Python", "Customer Support", "Git"]
    created_at = Column(DateTime, default=utc_now)

    onboarding_plans = relationship("OnboardingPlan", back_populates="employee")

class RoleRequirementMatrix(Base):
    __tablename__ = "role_requirement_matrices"

    id = Column(Integer, primary_key=True, index=True)
    role_code = Column(String(50), unique=True, index=True, nullable=False)
    role_title = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    required_skills = Column(JSON, default=list) # ["SOP-001", "Security Protocols", "Customer Escalation"]
    required_sops = Column(JSON, default=list) # ["POL-001", "POL-003", "SOP-LOG-02"]
    core_competencies = Column(JSON, default=list) # ["Product Knowledge", "Compliance", "Tooling"]
    minimum_passing_quiz_score = Column(Integer, default=80)
    onboarding_duration_days = Column(Integer, default=14)
    created_at = Column(DateTime, default=utc_now)

class OnboardingPlan(Base):
    __tablename__ = "onboarding_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String(50), unique=True, index=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employee_profiles.id"), nullable=False)
    role_title = Column(String(100), nullable=False)
    status = Column(String(50), default="GENERATED") # GENERATED, IN_PROGRESS, COMPLETED, MANUAL_REVIEW
    
    # GenAI Output (Pipeline 1)
    learning_modules = Column(JSON, default=list)
    checklists = Column(JSON, default=list)
    tasks = Column(JSON, default=list)
    quizzes = Column(JSON, default=list)
    assessments = Column(JSON, default=list)

    # Verification Decision & Scores (Pipeline 2 & Comparison)
    coverage_score = Column(Float, default=0.0)
    traceability_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    verification_status = Column(String(50), default="VERIFIED") # VERIFIED, WARNING, MANUAL_REVIEW
    contradictions_detected = Column(JSON, default=list)
    missing_requirements = Column(JSON, default=list)
    verified_sources = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)

    employee = relationship("EmployeeProfile", back_populates="onboarding_plans")

