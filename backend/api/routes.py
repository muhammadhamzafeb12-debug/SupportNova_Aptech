import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, status
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    User, Customer, Department, Category, Subcategory, RuleMatrix, Policy, DocumentChunk,
    Complaint, GenAIAnalysis, PythonValidation, Comparison, ManualReview, SLARecord,
    PromptTemplate, AuditLog, UserRole, ComplaintStatus, EmployeeProfile, RoleRequirementMatrix, OnboardingPlan
)
from backend.schemas.schemas import (
    Token, LoginRequest, UserCreate, UserOut, UserUpdateRole, UserUpdateStatus,
    ForgotPasswordRequest, ResetPasswordRequest, ComplaintCreate, ComplaintOut,
    ReviewActionCreate, PolicyCreate, RuleMatrixEntry, PromptTemplateSchema, ComparisonOut,
    StandaloneValidationRequest, EmployeeProfileCreate, EmployeeProfileOut, RoleRequirementMatrixCreate, RoleRequirementMatrixOut,
    OnboardingGenerateRequest, OnboardingPlanOut
)
from backend.skillsprint_engine.onboarding_engine import (
    run_pipeline_1_genai, run_pipeline_2_python_validation, compute_verification_decision
)
from backend.auth.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user, get_optional_current_user, require_roles
)
from backend.complaint_processing.preprocessor import (
    sanitize_input, detect_prompt_injection, check_duplicate_complaint
)
from backend.document_processing.document_processor import parse_pdf, parse_docx, parse_txt, chunk_document
from backend.knowledge_base.retrieval_engine import retrieve_relevant_policies
from backend.genai_pipeline.genai_engine import run_genai_analysis
from backend.python_validation.ground_truth_engine import evaluate_ground_truth
from backend.complaint_rules.ground_truth_validator import run_ground_truth_validation
from backend.comparison_engine.comparator import compare_genai_vs_python
from backend.sla.sla_engine import create_or_update_sla, evaluate_sla_status
from backend.reports.report_generator import generate_csv_complaints_report, generate_100_case_comparison_report

router = APIRouter()

# --- 1. AUTHENTICATION & USER MANAGEMENT ---

@router.post("/auth/token", response_model=Token, tags=["Authentication & Users"])
async def login_for_access_token(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    login_input = ""
    password = ""
    remember_me = False

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        login_input = str(form.get("username", "") or form.get("username_or_email", "")).strip()
        password = str(form.get("password", ""))
    else:
        try:
            payload = await request.json()
            login_input = str(payload.get("username_or_email", "") or payload.get("username", "")).strip()
            password = str(payload.get("password", ""))
            remember_me = bool(payload.get("remember_me", False))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request payload")

    if not login_input or not password:
        raise HTTPException(status_code=400, detail="Username/Email and Password are required")

    user = db.query(User).filter(
        (User.username == login_input) | (User.email == login_input)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        audit = AuditLog(
            username=login_input,
            action="LOGIN_FAILURE",
            entity_name="User",
            details={"reason": "Invalid credentials provided"}
        )
        db.add(audit)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email/username or password")

    if not user.is_active:
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action="LOGIN_BLOCKED",
            entity_name="User",
            details={"reason": "Account is disabled"}
        )
        db.add(audit)
        db.commit()
        raise HTTPException(status_code=403, detail="Account disabled. Please contact your system administrator.")

    user.last_login = datetime.utcnow()
    
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="LOGIN_SUCCESS",
        entity_name="User",
        entity_id=str(user.id),
        details={"role": user.role, "remember_me": remember_me}
    )
    db.add(audit)
    db.commit()

    expires = timedelta(days=30) if remember_me else None
    access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=expires)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active
    }

@router.post("/auth/register", response_model=UserOut, tags=["Authentication & Users"])
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if not user_in.username or not user_in.email or not user_in.password:
        raise HTTPException(status_code=400, detail="All fields are required")
        
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=user_in.username.strip(),
        email=user_in.email.strip().lower(),
        full_name=user_in.full_name.strip(),
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        department_id=user_in.department_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_REGISTER",
        entity_name="User",
        entity_id=str(user.id),
        details={"role": user.role, "email": user.email}
    )
    db.add(audit)
    db.commit()

    return user

@router.post("/auth/logout", tags=["Authentication & Users"])
def logout_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="LOGOUT",
        entity_name="User",
        entity_id=str(current_user.id),
        details={"timestamp": datetime.utcnow().isoformat()}
    )
    db.add(audit)
    db.commit()
    return {"message": "Successfully logged out"}

@router.post("/auth/forgot-password", tags=["Authentication & Users"])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == req.email_or_username) | (User.email == req.email_or_username)
    ).first()
    
    if not user:
        # Return generic message to prevent account enumeration
        return {"message": "If the account exists, a password reset mechanism has been initialized.", "demo_code": "RESET-2026-DEMO"}

    demo_reset_code = f"RESET-{user.username.upper()}-2026"
    
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="PASSWORD_RESET_REQUEST",
        entity_name="User",
        entity_id=str(user.id),
        details={"demo_reset_code": demo_reset_code}
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Password reset code generated successfully (Demo Mode)",
        "username": user.username,
        "demo_reset_code": demo_reset_code
    }

@router.post("/auth/reset-password", tags=["Authentication & Users"])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
    user = db.query(User).filter(
        (User.username == req.token_or_username) | (User.email == req.token_or_username)
    ).first()

    if not user and "RESET-" in req.token_or_username:
        # Extract username from reset code if format RESET-USERNAME-2026
        parts = req.token_or_username.split("-")
        if len(parts) >= 2:
            u_name = parts[1].lower()
            user = db.query(User).filter(User.username == u_name).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or reset token")

    user.hashed_password = get_password_hash(req.new_password)
    user.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="PASSWORD_RESET_SUCCESS",
        entity_name="User",
        entity_id=str(user.id),
        details={"message": "Password successfully updated"}
    )
    db.add(audit)
    db.commit()

    return {"message": "Password reset successfully. You can now login with your new password."}

# Admin User Management API
@router.get("/users", response_model=List[UserOut], tags=["Authentication & Users"])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return db.query(User).order_by(User.id.asc()).all()

@router.put("/users/{id}/role", tags=["Authentication & Users"])
def update_user_role(
    id: int,
    payload: UserUpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_role = user.role
    user.role = payload.role
    user.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ROLE_CHANGE",
        entity_name="User",
        entity_id=str(user.id),
        details={"target_username": user.username, "old_role": old_role, "new_role": payload.role}
    )
    db.add(audit)
    db.commit()
    return {"message": f"User role updated to '{payload.role}'", "user_id": user.id}

@router.put("/users/{id}/status", tags=["Authentication & Users"])
def update_user_status(
    id: int,
    payload: UserUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = payload.is_active
    user.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ACCOUNT_STATUS_CHANGE",
        entity_name="User",
        entity_id=str(user.id),
        details={"target_username": user.username, "is_active": payload.is_active}
    )
    db.add(audit)
    db.commit()
    return {"message": f"User account {'enabled' if payload.is_active else 'disabled'}", "user_id": user.id}

# --- 2. COMPLAINT SUBMISSION & MANAGEMENT ---
@router.post("/complaints", response_model=ComplaintOut, tags=["Complaints & Dual-Pipeline Engine"])
def submit_complaint(
    comp_in: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    # Pre-processing & Sanitization (SRS requirement #8)
    clean_title = sanitize_input(comp_in.title)
    clean_desc = sanitize_input(comp_in.description)
    
    if len(clean_desc) < 10:
        raise HTTPException(status_code=400, detail="Complaint description is too short. Please provide details.")

    # Prompt Injection Defense (SRS requirement #37)
    prompt_inj_flag = detect_prompt_injection(clean_desc) or detect_prompt_injection(clean_title)

    # Duplicate & Near-duplicate Detection (SRS requirement #39)
    is_dup, dup_code = check_duplicate_complaint(db, clean_title, clean_desc)

    # Generate unique complaint code
    count = db.query(Complaint).count() + 1
    code = f"CMP-{2026000 + count}"

    # Resolve customer
    cust_id = comp_in.customer_id
    if not cust_id:
        cust = db.query(Customer).filter(Customer.email == (comp_in.customer_email or "customer@gmail.com")).first()
        if cust:
            cust_id = cust.id

    complaint = Complaint(
        complaint_code=code,
        title=clean_title,
        description=clean_desc,
        customer_id=cust_id,
        customer_type=comp_in.customer_type or "REGULAR",
        product_service=comp_in.product_service,
        order_ref=comp_in.order_ref,
        transaction_ref=comp_in.transaction_ref,
        prev_complaint_ref=comp_in.prev_complaint_ref,
        channel=comp_in.channel or "WEB_FORM",
        preferred_contact=comp_in.preferred_contact or "EMAIL",
        status=ComplaintStatus.NEW.value,
        is_duplicate=is_dup,
        duplicate_of_code=dup_code,
        prompt_injection_flag=prompt_inj_flag
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Setup SLA record
    create_or_update_sla(db, complaint, complaint.priority)

    # Audit Log
    username = current_user.username if current_user else "ANONYMOUS_CUSTOMER"
    audit = AuditLog(
        username=username,
        complaint_code=code,
        action="SUBMIT_COMPLAINT",
        entity_name="Complaint",
        entity_id=str(complaint.id),
        details={"title": clean_title, "is_duplicate": is_dup, "prompt_injection_flag": prompt_inj_flag}
    )
    db.add(audit)
    db.commit()

    return complaint

@router.get("/complaints", tags=["Complaints & Dual-Pipeline Engine"])
def list_complaints(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Complaint)
    
    # If customer role, only return own submitted complaints
    if current_user.role == UserRole.CUSTOMER.value:
        cust = db.query(Customer).filter(Customer.email == current_user.email).first()
        if cust:
            query = query.filter(Complaint.customer_id == cust.id)
            
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if search:
        query = query.filter((Complaint.title.contains(search)) | (Complaint.description.contains(search)) | (Complaint.complaint_code.contains(search)))
        
    complaints = query.order_by(Complaint.id.desc()).all()
    
    result = []
    for c in complaints:
        comp_status = c.comparison.overall_status if c.comparison else "NOT ANALYZED"
        score = c.comparison.overall_verification_score if c.comparison else 0.0
        result.append({
            "id": c.id,
            "complaint_code": c.complaint_code,
            "title": c.title,
            "description": c.description,
            "customer_type": c.customer_type,
            "product_service": c.product_service,
            "order_ref": c.order_ref,
            "submitted_at": c.submitted_at,
            "status": c.status,
            "priority": c.priority,
            "urgency": c.urgency,
            "sentiment": c.sentiment,
            "category": c.genai_analysis.category if c.genai_analysis else "N/A",
            "department": c.genai_analysis.department if c.genai_analysis else "N/A",
            "comparison_status": comp_status,
            "verification_score": score,
            "is_duplicate": c.is_duplicate,
            "prompt_injection_flag": c.prompt_injection_flag
        })
    return result

@router.get("/complaints/{id}", tags=["Complaints & Dual-Pipeline Engine"])
def get_complaint_details(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    genai = c.genai_analysis
    py_val = c.python_validation
    comp = c.comparison
    reviews = c.manual_reviews
    sla = c.sla_record
    
    return {
        "complaint": c,
        "genai_analysis": genai,
        "python_validation": py_val,
        "comparison": comp,
        "manual_reviews": reviews,
        "sla": {
            "response_deadline": sla.response_deadline if sla else None,
            "resolution_deadline": sla.resolution_deadline if sla else None,
            "status": evaluate_sla_status(sla) if sla else "ON_TRACK"
        }
    }

# --- 3. DUAL-PIPELINE AI ANALYSIS & GROUND-TRUTH ENGINE ---
@router.post("/complaints/{id}/analyze", tags=["Complaints & Dual-Pipeline Engine"])
def analyze_complaint(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Step 1: Semantic Retrieval of Approved Policies
    relevant_policies = retrieve_relevant_policies(db, c.description, top_k=3)

    # Step 2: Pipeline 1 - Generative AI Analysis
    genai_res = run_genai_analysis(c.complaint_code, c.title, c.description, relevant_policies)

    # Save/Update GenAI Analysis
    g_db = db.query(GenAIAnalysis).filter(GenAIAnalysis.complaint_id == c.id).first()
    if not g_db:
        g_db = GenAIAnalysis(complaint_id=c.id, provider="mock", model="supportnova-model-v1")
        db.add(g_db)
        
    g_db.primary_issue = genai_res.primary_issue
    g_db.secondary_issues = genai_res.secondary_issues
    g_db.category = genai_res.category
    g_db.subcategory = genai_res.subcategory
    g_db.sentiment = genai_res.sentiment
    g_db.urgency = genai_res.urgency
    g_db.priority = genai_res.priority
    g_db.entities = genai_res.entities
    g_db.department = genai_res.department
    g_db.supporting_departments = genai_res.supporting_departments
    g_db.policy_references = genai_res.policy_references
    g_db.resolution_steps = genai_res.resolution_steps
    g_db.escalation_required = genai_res.escalation_required
    g_db.escalation_level = genai_res.escalation_level
    g_db.escalation_reason = genai_res.escalation_reason
    g_db.customer_response = genai_res.customer_response
    g_db.follow_up_required = genai_res.follow_up_required
    g_db.follow_up_message = genai_res.follow_up_message
    g_db.clarification_questions = genai_res.clarification_questions
    g_db.agent_guidance = genai_res.agent_guidance
    g_db.raw_json_output = genai_res.json()

    # Step 3: Pipeline 2 - Independent Python Ground-Truth Validation
    py_res = evaluate_ground_truth(db, c.title, c.description, genai_res, c.customer_type, c.prev_complaint_ref)

    py_db = db.query(PythonValidation).filter(PythonValidation.complaint_id == c.id).first()
    if not py_db:
        py_db = PythonValidation(complaint_id=c.id)
        db.add(py_db)
        
    py_db.rule_id_matched = py_res.rule_id_matched
    py_db.verified_category = py_res.verified_category
    py_db.verified_subcategory = py_res.verified_subcategory
    py_db.verified_department = py_res.verified_department
    py_db.verified_urgency = py_res.verified_urgency
    py_db.verified_priority = py_res.verified_priority
    py_db.verified_escalation_required = py_res.verified_escalation_required
    py_db.verified_escalation_level = py_res.verified_escalation_level
    py_db.verified_escalation_reason = py_res.verified_escalation_reason
    py_db.verified_refund_eligible = py_res.verified_refund_eligible
    py_db.verified_replacement_eligible = py_res.verified_replacement_eligible
    py_db.verified_compensation_eligible = py_res.verified_compensation_eligible
    py_db.mandatory_actions = py_res.mandatory_actions
    py_db.prohibited_actions = py_res.prohibited_actions
    py_db.policy_grounding_valid = py_res.policy_grounding_valid
    py_db.unsupported_claims = py_res.unsupported_claims
    py_db.contradictions = py_res.contradictions
    py_db.missing_actions = py_res.missing_actions

    # Step 4: Comparison & Verification Engine
    comp_res = compare_genai_vs_python(genai_res, py_res)

    comp_db = db.query(Comparison).filter(Comparison.complaint_id == c.id).first()
    if not comp_db:
        comp_db = Comparison(complaint_id=c.id)
        db.add(comp_db)
        
    comp_db.overall_status = comp_res[0]
    comp_db.schema_compliance_score = comp_res[1]
    comp_db.policy_compliance_score = comp_res[2]
    comp_db.routing_compliance_score = comp_res[3]
    comp_db.urgency_compliance_score = comp_res[4]
    comp_db.escalation_compliance_score = comp_res[5]
    comp_db.resolution_compliance_score = comp_res[6]
    comp_db.source_traceability_score = comp_res[7]
    comp_db.overall_verification_score = comp_res[8]
    comp_db.mismatches = [m.dict() for m in comp_res[9]]

    # Update Complaint fields
    c.status = ComplaintStatus.ANALYZED.value
    c.priority = py_res.verified_priority
    c.urgency = py_res.verified_urgency
    c.sentiment = genai_res.sentiment

    # If critical mismatch or escalation required, auto-flag for manual review or escalation
    if comp_res[0] in ["MISMATCH", "REVIEW REQUIRED"] or py_res.verified_escalation_required:
        c.status = ComplaintStatus.ESCALATED.value

    # Update SLA
    create_or_update_sla(db, c, c.priority)

    db.commit()

    return {
        "complaint_code": c.complaint_code,
        "genai_analysis": genai_res,
        "python_validation": py_res,
        "comparison_status": comp_res[0],
        "overall_verification_score": comp_res[8],
        "mismatches": [m.dict() for m in comp_res[9]]
    }

# --- 4. MANUAL REVIEW QUEUE & ACTIONS ---
@router.get("/reviews", tags=["Manual Review Queue"])
def get_manual_review_queue(db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.MANAGER, UserRole.ADMIN]))):
    # Fetch complaints with MISMATCH, REVIEW REQUIRED status or ESCALATED
    query = db.query(Complaint, Comparison).join(Comparison, Complaint.id == Comparison.complaint_id).filter(
        (Comparison.overall_status.in_(["MISMATCH", "REVIEW REQUIRED"])) | (Complaint.status == ComplaintStatus.ESCALATED.value)
    ).all()
    
    queue = []
    for c, comp in query:
        queue.append({
            "id": c.id,
            "complaint_code": c.complaint_code,
            "title": c.title,
            "customer_type": c.customer_type,
            "submitted_at": c.submitted_at,
            "status": c.status,
            "genai_category": c.genai_analysis.category if c.genai_analysis else "N/A",
            "python_category": c.python_validation.verified_category if c.python_validation else "N/A",
            "overall_status": comp.overall_status,
            "overall_verification_score": comp.overall_verification_score,
            "mismatch_count": len(comp.mismatches or [])
        })
    return queue

@router.post("/complaints/{id}/review", tags=["Manual Review Queue"])
def submit_manual_review(
    id: int,
    review_in: ReviewActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.REVIEWER, UserRole.MANAGER, UserRole.ADMIN]))
):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    review = ManualReview(
        complaint_id=c.id,
        reviewer_id=current_user.id,
        review_reason="Manual override by authorized reviewer",
        reviewer_action=review_in.reviewer_action,
        modified_category=review_in.modified_category,
        modified_department=review_in.modified_department,
        modified_escalation_level=review_in.modified_escalation_level,
        reviewer_comments=review_in.reviewer_comments
    )
    db.add(review)

    # Update Complaint state based on decision
    if review_in.reviewer_action == "APPROVE":
        c.status = ComplaintStatus.IN_PROGRESS.value
    elif review_in.reviewer_action == "REJECT":
        c.status = ComplaintStatus.CLOSED.value
    elif review_in.reviewer_action == "ESCALATE":
        c.status = ComplaintStatus.ESCALATED.value

    db.commit()
    return {"message": "Review decision recorded successfully", "status": c.status}

# --- 5. KNOWLEDGE BASE & POLICY MANAGEMENT ---
@router.get("/policies", tags=["Knowledge Base & Policy Rules"])
def list_policies(db: Session = Depends(get_db)):
    return db.query(Policy).all()

@router.get("/policies/{id}/chunks", tags=["Knowledge Base & Policy Rules"])
def get_policy_chunks(id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    chunks = db.query(DocumentChunk).filter(DocumentChunk.policy_id == policy.id).all()
    return {
        "policy_id": policy.id,
        "doc_id": policy.doc_id,
        "title": policy.title,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "id": c.id,
                "section_id": c.section_id,
                "heading": c.heading,
                "page_number": c.page_number,
                "version": c.version,
                "content": c.content
            } for c in chunks
        ]
    }

@router.post("/policies/upload", tags=["Knowledge Base & Policy Rules"])
async def upload_policy_document(
    title: str = Form(...),
    category: str = Form(...),
    version: str = Form("1.0"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    # Check if uploaded file is 0 bytes / empty
    file_bytes = await file.read()
    if not file_bytes or len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file. The uploaded file is empty and contains no data."
        )

    # Save file
    os.makedirs("./data/uploads", exist_ok=True)
    file_path = f"./data/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Extract text content
    ext = os.path.splitext(file.filename)[1].lower()
    if ext == ".pdf":
        pages = parse_pdf(file_path)
        content = "\n".join([p["text"] for p in pages])
    elif ext in [".docx", ".doc"]:
        sections = parse_docx(file_path)
        content = "\n".join([s["text"] for s in sections])
    else:
        content = parse_txt(file_path)

    if not content or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Empty file. The uploaded document contains no readable text."
        )

    doc_id = f"POL-UPL-{db.query(Policy).count() + 1:03d}"
    policy = Policy(
        doc_id=doc_id,
        title=title,
        category=category,
        status="ACTIVE",
        version=version,
        content=content,
        file_path=file_path,
        file_type=ext.replace(".", "").upper(),
        source_reference=f"Uploaded Document: {file.filename}"
    )
    db.add(policy)
    db.flush()

    # Chunk policy
    chunks = chunk_document(doc_id, title, content, version)
    for c_data in chunks:
        chunk_obj = DocumentChunk(
            policy_id=policy.id,
            doc_id=doc_id,
            section_id=c_data["section_id"],
            heading=c_data["heading"],
            page_number=c_data["page_number"],
            version=version,
            content=c_data["content"]
        )
        db.add(chunk_obj)
        
    db.commit()
    return {"message": "Policy uploaded and chunked successfully", "doc_id": doc_id, "chunk_count": len(chunks)}

# --- 6. RULE MATRIX MANAGEMENT ---
@router.get("/rules", tags=["Knowledge Base & Policy Rules"])
def get_rule_matrix(db: Session = Depends(get_db)):
    return db.query(RuleMatrix).all()

# --- 7. PROMPT MANAGEMENT ---
@router.get("/prompts", tags=["Knowledge Base & Policy Rules"])
def get_prompts(db: Session = Depends(get_db)):
    return db.query(PromptTemplate).all()

# --- 8. ANALYTICS & DASHBOARDS ---
@router.get("/analytics/summary", tags=["Analytics & Reports"])
def get_analytics_summary(db: Session = Depends(get_db)):
    total = db.query(Complaint).count()
    analyzed = db.query(Complaint).filter(Complaint.status == "ANALYZED").count()
    escalated = db.query(Complaint).filter(Complaint.status == "ESCALATED").count()
    resolved = db.query(Complaint).filter(Complaint.status == "RESOLVED").count()
    
    matches = db.query(Comparison).filter(Comparison.overall_status == "MATCH").count()
    mismatches = db.query(Comparison).filter(Comparison.overall_status == "MISMATCH").count()
    reviews = db.query(Comparison).filter(Comparison.overall_status == "REVIEW REQUIRED").count()
    
    # Priority breakdown
    p0 = db.query(Complaint).filter(Complaint.priority.contains("P0")).count()
    p1 = db.query(Complaint).filter(Complaint.priority.contains("P1")).count()
    p2 = db.query(Complaint).filter(Complaint.priority.contains("P2")).count()
    p3 = db.query(Complaint).filter(Complaint.priority.contains("P3")).count()

    return {
        "overview": {
            "total_complaints": total,
            "analyzed": analyzed,
            "escalated": escalated,
            "resolved": resolved,
            "agreement_rate": round((matches / total) * 100, 2) if total > 0 else 100.0
        },
        "comparison_breakdown": {
            "matches": matches,
            "mismatches": mismatches,
            "reviews_required": reviews
        },
        "priority_breakdown": {
            "P0_Critical": p0,
            "P1_High": p1,
            "P2_Medium": p2,
            "P3_Low": p3
        }
    }

# --- 9. REPORTS & EXPORTS ---
@router.get("/reports/csv", tags=["Analytics & Reports"])
def download_csv_report(db: Session = Depends(get_db)):
    csv_data = generate_csv_complaints_report(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=SupportNova_Complaints_Report.csv"}
    )

@router.get("/reports/100-case-evaluation", tags=["Analytics & Reports"])
def get_100_case_report(db: Session = Depends(get_db)):
    return generate_100_case_comparison_report(db)

# --- 10. AUDIT LOGS ---
@router.get("/audit-logs", tags=["Audit Logs"])
def list_audit_logs(db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN]))):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

# --- 11. SKILLSPRINT AI ONBOARDING & ROLE MATRIX ROUTES ---

@router.get("/skillsprint/employees", response_model=List[EmployeeProfileOut], tags=["SkillSprint AI"])
def list_employees(db: Session = Depends(get_db)):
    return db.query(EmployeeProfile).order_by(EmployeeProfile.created_at.desc()).all()

@router.post("/skillsprint/employees", response_model=EmployeeProfileOut, tags=["SkillSprint AI"])
def create_employee_profile(emp_in: EmployeeProfileCreate, db: Session = Depends(get_db)):
    count = db.query(EmployeeProfile).count() + 1
    code = emp_in.employee_code or f"EMP-{2026000 + count}"
    
    emp = EmployeeProfile(
        employee_code=code,
        full_name=emp_in.full_name,
        email=emp_in.email,
        department=emp_in.department,
        role_title=emp_in.role_title,
        seniority_level=emp_in.seniority_level or "Junior",
        prior_experience_years=emp_in.prior_experience_years or 0.0,
        current_skills=emp_in.current_skills or []
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

@router.get("/skillsprint/roles", response_model=List[RoleRequirementMatrixOut], tags=["SkillSprint AI"])
def list_role_matrices(db: Session = Depends(get_db)):
    return db.query(RoleRequirementMatrix).all()

@router.post("/skillsprint/roles", response_model=RoleRequirementMatrixOut, tags=["SkillSprint AI"])
def create_role_requirement_matrix(role_in: RoleRequirementMatrixCreate, db: Session = Depends(get_db)):
    existing = db.query(RoleRequirementMatrix).filter(RoleRequirementMatrix.role_code == role_in.role_code).first()
    if existing:
        existing.role_title = role_in.role_title
        existing.department = role_in.department
        existing.required_skills = role_in.required_skills
        existing.required_sops = role_in.required_sops
        existing.core_competencies = role_in.core_competencies
        db.commit()
        db.refresh(existing)
        return existing

    matrix = RoleRequirementMatrix(
        role_code=role_in.role_code,
        role_title=role_in.role_title,
        department=role_in.department,
        required_skills=role_in.required_skills,
        required_sops=role_in.required_sops,
        core_competencies=role_in.core_competencies,
        minimum_passing_quiz_score=role_in.minimum_passing_quiz_score or 80,
        onboarding_duration_days=role_in.onboarding_duration_days or 14
    )
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    return matrix

@router.post("/skillsprint/onboarding/generate", response_model=OnboardingPlanOut, tags=["SkillSprint AI"])
def generate_skillsprint_onboarding_plan(req: OnboardingGenerateRequest, db: Session = Depends(get_db)):
    emp = db.query(EmployeeProfile).filter(EmployeeProfile.id == req.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    matrix = db.query(RoleRequirementMatrix).filter(RoleRequirementMatrix.role_code == req.role_code).first()
    if not matrix:
        # Fallback default matrix
        matrix_dict = {
            "role_title": emp.role_title,
            "department": emp.department,
            "required_skills": ["SOP-001", "Security Compliance", "Workflow Execution"],
            "required_sops": ["POL-001", "SOP-LOG-01"],
            "minimum_passing_quiz_score": 80
        }
    else:
        matrix_dict = {
            "role_title": matrix.role_title,
            "department": matrix.department,
            "required_skills": matrix.required_skills,
            "required_sops": matrix.required_sops,
            "minimum_passing_quiz_score": matrix.minimum_passing_quiz_score
        }

    # Fetch knowledge chunks
    chunks = db.query(DocumentChunk).all()
    chunk_dicts = [{"doc_id": c.doc_id, "heading": c.heading, "content": c.content} for c in chunks]

    # Pipeline 1: GenAI API Plan Generation
    emp_dict = {
        "full_name": emp.full_name,
        "role_title": emp.role_title,
        "department": emp.department,
        "seniority_level": emp.seniority_level
    }
    genai_plan = run_pipeline_1_genai(emp_dict, matrix_dict, chunk_dicts)

    # Pipeline 2: Ground-Truth Python Validation
    val_res = run_pipeline_2_python_validation(emp_dict, matrix_dict, genai_plan, chunk_dicts)

    # Compute Verification Decision
    ver_status = compute_verification_decision(val_res)

    plan_code = f"SKP-PLAN-{db.query(OnboardingPlan).count() + 1:04d}"

    plan = OnboardingPlan(
        plan_code=plan_code,
        employee_id=emp.id,
        role_title=emp.role_title,
        status="GENERATED",
        learning_modules=genai_plan.get("learning_modules", []),
        checklists=genai_plan.get("checklists", []),
        tasks=genai_plan.get("tasks", []),
        quizzes=genai_plan.get("quizzes", []),
        assessments=genai_plan.get("assessments", []),
        coverage_score=val_res.get("coverage_score", 0.0),
        traceability_score=val_res.get("traceability_score", 0.0),
        consistency_score=val_res.get("consistency_score", 0.0),
        verification_status=ver_status,
        contradictions_detected=val_res.get("contradictions_detected", []),
        missing_requirements=val_res.get("missing_requirements", []),
        verified_sources=val_res.get("verified_sources", [])
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/skillsprint/onboarding/plans", response_model=List[OnboardingPlanOut], tags=["SkillSprint AI"])
def list_onboarding_plans(db: Session = Depends(get_db)):
    return db.query(OnboardingPlan).order_by(OnboardingPlan.created_at.desc()).all()

@router.get("/skillsprint/onboarding/plans/{id}", response_model=OnboardingPlanOut, tags=["SkillSprint AI"])
def get_onboarding_plan(id: int, db: Session = Depends(get_db)):
    plan = db.query(OnboardingPlan).filter(OnboardingPlan.id == id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Onboarding plan not found")
    return plan

# --- PIPELINE 2: INDEPENDENT PYTHON GROUND-TRUTH ENDPOINTS ---

@router.post("/pipeline2/validate", tags=["Pipeline 2 Ground Truth"])
def standalone_python_validation(req: StandaloneValidationRequest, db: Session = Depends(get_db)):
    """Runs independent Python ground-truth validation engine on complaint input text."""
    res = run_ground_truth_validation(
        db=db,
        complaint_title=req.complaint_title,
        complaint_description=req.complaint_description,
        genai_output=req.genai_output,
        customer_type=req.customer_type or "REGULAR",
        prev_complaint_ref=req.prev_complaint_ref,
        warranty_status=req.warranty_status or "ACTIVE",
        defect_condition=req.defect_condition
    )
    return res

@router.post("/pipeline2/compare", tags=["Pipeline 2 Ground Truth"])
def standalone_compare_genai_vs_python(
    genai_output: GenAIResponseSchema,
    python_output: PythonValidationSchema
):
    """Compares GenAI Pipeline 1 output vs Python Ground-Truth Pipeline 2 output."""
    comp_res = compare_genai_vs_python(genai_output, python_output)
    mismatches_dict = [m.model_dump() if hasattr(m, 'model_dump') else m.dict() for m in comp_res[9]]
    return {
        "overall_status": comp_res[0],
        "schema_compliance_score": comp_res[1],
        "policy_compliance_score": comp_res[2],
        "routing_compliance_score": comp_res[3],
        "urgency_compliance_score": comp_res[4],
        "escalation_compliance_score": comp_res[5],
        "resolution_compliance_score": comp_res[6],
        "source_traceability_score": comp_res[7],
        "overall_verification_score": comp_res[8],
        "mismatches": mismatches_dict
    }

@router.get("/pipeline2/rules", response_model=List[RuleMatrixEntry], tags=["Pipeline 2 Ground Truth"])
def list_rule_matrix_entries(db: Session = Depends(get_db)):
    """Retrieves all 100+ structured rules in the Rule Matrix."""
    return db.query(RuleMatrix).filter(RuleMatrix.is_active == True).all()

@router.post("/pipeline2/rules", response_model=RuleMatrixEntry, tags=["Pipeline 2 Ground Truth"])
def create_or_update_rule_matrix_entry(
    entry: RuleMatrixEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.MANAGER.value]))
):
    """Creates or updates a Rule Matrix entry (Admin / Manager authorized)."""
    existing = db.query(RuleMatrix).filter(RuleMatrix.rule_id == entry.rule_id).first()
    if existing:
        existing.category = entry.category
        existing.subcategory = entry.subcategory
        existing.conditions = entry.conditions
        existing.department = entry.department
        existing.urgency = entry.urgency
        existing.priority = entry.priority
        existing.policy_doc_id = entry.policy_doc_id
        existing.policy_section = entry.policy_section
        existing.escalation_required = entry.escalation_required
        existing.escalation_level = entry.escalation_level
        existing.required_actions = entry.required_actions
        existing.prohibited_actions = entry.prohibited_actions
        existing.refund_eligible = entry.refund_eligible
        existing.replacement_eligible = entry.replacement_eligible
        existing.compensation_eligible = entry.compensation_eligible
        existing.follow_up_required = entry.follow_up_required
        existing.sla_hours = entry.sla_hours
        existing.rule_priority = entry.rule_priority
        existing.is_active = entry.is_active
        existing.version = entry.version
        db.commit()
        db.refresh(existing)
        return existing

    new_rule = RuleMatrix(
        rule_id=entry.rule_id,
        category=entry.category,
        subcategory=entry.subcategory,
        conditions=entry.conditions,
        department=entry.department,
        urgency=entry.urgency,
        priority=entry.priority,
        policy_doc_id=entry.policy_doc_id,
        policy_section=entry.policy_section,
        escalation_required=entry.escalation_required,
        escalation_level=entry.escalation_level,
        required_actions=entry.required_actions,
        prohibited_actions=entry.prohibited_actions,
        refund_eligible=entry.refund_eligible,
        replacement_eligible=entry.replacement_eligible,
        compensation_eligible=entry.compensation_eligible,
        follow_up_required=entry.follow_up_required,
        sla_hours=entry.sla_hours,
        rule_priority=entry.rule_priority,
        is_active=entry.is_active,
        version=entry.version
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.get("/complaints/{id}/validation-result", tags=["Pipeline 2 Ground Truth"])
def get_complaint_validation_and_comparison(id: int, db: Session = Depends(get_db)):
    """Retrieves full Dual-Pipeline GenAI analysis, Python ground truth validation, and comparison mismatch details."""
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    py_val = db.query(PythonValidation).filter(PythonValidation.complaint_id == c.id).first()
    comp_val = db.query(Comparison).filter(Comparison.complaint_id == c.id).first()
    genai_val = db.query(GenAIAnalysis).filter(GenAIAnalysis.complaint_id == c.id).first()

    return {
        "complaint_id": c.id,
        "complaint_code": c.complaint_code,
        "genai_analysis": genai_val,
        "python_validation": py_val,
        "comparison": comp_val
    }


