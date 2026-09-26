import os
import shutil
from datetime import datetime, timedelta
from typing import Optional, List
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from jose import jwt, JWTError
import bcrypt

from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.database_seed import seed_database
from backend.models import (
    User, Customer, Department, Category, Subcategory, RuleMatrix, Policy, DocumentChunk,
    Complaint, GenAIAnalysis, PythonValidation, Comparison, ManualReview, SLARecord,
    PromptTemplate, AuditLog, UserRole, ComplaintStatus
)
from backend.auth.auth import verify_password, get_password_hash, create_access_token
from backend.complaint_processing.preprocessor import sanitize_input, detect_prompt_injection, check_duplicate_complaint
from backend.document_processing.document_processor import parse_pdf, parse_docx, parse_txt, chunk_document
from backend.knowledge_base.retrieval_engine import retrieve_relevant_policies
from backend.genai_pipeline.genai_engine import run_genai_analysis
from backend.python_validation.ground_truth_engine import evaluate_ground_truth
from backend.comparison_engine.comparator import compare_genai_vs_python
from backend.sla.sla_engine import create_or_update_sla, evaluate_sla_status
from backend.reports.report_generator import generate_csv_complaints_report, generate_100_case_comparison_report

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})

# DB Helper for Flask Request Scope
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def close_db(db):
    if db:
        db.close()

def get_current_user_from_req(db):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        user = db.query(User).filter(User.username == username).first()
        if user and not user.is_active:
            return None
        return user
    except Exception:
        return None

def require_auth(db, allowed_roles=None):
    user = get_current_user_from_req(db)
    if not user:
        return None, (jsonify({"detail": "Authentication required or token expired"}), 401)
    if allowed_roles:
        role_vals = [r.value if hasattr(r, 'value') else r for r in allowed_roles]
        if user.role not in role_vals and user.role != UserRole.ADMIN.value:
            return None, (jsonify({"detail": f"Forbidden: Required roles {role_vals}"}), 403)
    return user, None

# --- ROOT & HEALTHCHECK ---
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "app": settings.APP_NAME,
        "framework": "Flask (Python)",
        "status": "ONLINE",
        "organization": "NovaCart Technologies",
        "version": "1.0.0"
    })

# --- 1. AUTHENTICATION & USER MANAGEMENT ---
@app.route("/api/auth/token", methods=["POST"])
def login_for_access_token():
    db = get_db()
    try:
        data = request.get_json() or {}
        username_or_email = data.get("username_or_email", "").strip()
        password = data.get("password", "")
        remember_me = data.get("remember_me", False)

        if not username_or_email or not password:
            return jsonify({"detail": "Username/Email and Password are required"}), 400

        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user or not verify_password(password, user.hashed_password):
            audit = AuditLog(
                username=username_or_email,
                action="LOGIN_FAILURE",
                entity_name="User",
                details={"reason": "Invalid credentials provided"}
            )
            db.add(audit)
            db.commit()
            return jsonify({"detail": "Invalid email/username or password"}), 401

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
            return jsonify({"detail": "Account disabled. Please contact your system administrator."}), 403

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

        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active
        })
    finally:
        close_db(db)

@app.route("/api/auth/register", methods=["POST"])
def register_user():
    db = get_db()
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        full_name = data.get("full_name", "").strip()
        password = data.get("password", "")
        role = data.get("role", "CUSTOMER")
        department_id = data.get("department_id")

        if not username or not email or not password:
            return jsonify({"detail": "Username, Email, and Password are required"}), 400

        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            return jsonify({"detail": "Username or email already registered"}), 400

        user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            hashed_password=get_password_hash(password),
            role=role,
            department_id=department_id,
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

        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active
        })
    finally:
        close_db(db)

@app.route("/api/auth/logout", methods=["POST"])
def logout_user():
    db = get_db()
    try:
        user, err = require_auth(db)
        if err:
            return err
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action="LOGOUT",
            entity_name="User",
            entity_id=str(user.id),
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        db.add(audit)
        db.commit()
        return jsonify({"message": "Successfully logged out"})
    finally:
        close_db(db)

@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    db = get_db()
    try:
        data = request.get_json() or {}
        val = data.get("email_or_username", "").strip()
        user = db.query(User).filter((User.username == val) | (User.email == val)).first()
        if not user:
            return jsonify({"message": "If the account exists, a password reset mechanism has been initialized.", "demo_code": "RESET-2026-DEMO"})

        demo_code = f"RESET-{user.username.upper()}-2026"
        audit = AuditLog(
            user_id=user.id,
            username=user.username,
            action="PASSWORD_RESET_REQUEST",
            entity_name="User",
            entity_id=str(user.id),
            details={"demo_reset_code": demo_code}
        )
        db.add(audit)
        db.commit()
        return jsonify({
            "message": "Password reset code generated successfully (Demo Mode)",
            "username": user.username,
            "demo_reset_code": demo_code
        })
    finally:
        close_db(db)

@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    db = get_db()
    try:
        data = request.get_json() or {}
        token_or_username = data.get("token_or_username", "").strip()
        new_password = data.get("new_password", "")

        if len(new_password) < 6:
            return jsonify({"detail": "Password must be at least 6 characters long"}), 400

        user = db.query(User).filter(
            (User.username == token_or_username) | (User.email == token_or_username)
        ).first()

        if not user and "RESET-" in token_or_username:
            parts = token_or_username.split("-")
            if len(parts) >= 2:
                u_name = parts[1].lower()
                user = db.query(User).filter(User.username == u_name).first()

        if not user:
            return jsonify({"detail": "Invalid username or reset token"}), 400

        user.hashed_password = get_password_hash(new_password)
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
        return jsonify({"message": "Password reset successfully. You can now login with your new password."})
    finally:
        close_db(db)

# Admin User Management API
@app.route("/api/users", methods=["GET"])
def list_users():
    db = get_db()
    try:
        user, err = require_auth(db, [UserRole.ADMIN])
        if err:
            return err
        users = db.query(User).order_by(User.id.asc()).all()
        return jsonify([{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None
        } for u in users])
    finally:
        close_db(db)

@app.route("/api/users/<int:user_id>/role", methods=["PUT"])
def update_user_role(user_id):
    db = get_db()
    try:
        admin_user, err = require_auth(db, [UserRole.ADMIN])
        if err:
            return err
        data = request.get_json() or {}
        new_role = data.get("role")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"detail": "User not found"}), 404

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        audit = AuditLog(
            user_id=admin_user.id,
            username=admin_user.username,
            action="ROLE_CHANGE",
            entity_name="User",
            entity_id=str(user.id),
            details={"target_username": user.username, "old_role": old_role, "new_role": new_role}
        )
        db.add(audit)
        db.commit()
        return jsonify({"message": f"User role updated to '{new_role}'", "user_id": user.id})
    finally:
        close_db(db)

@app.route("/api/users/<int:user_id>/status", methods=["PUT"])
def update_user_status(user_id):
    db = get_db()
    try:
        admin_user, err = require_auth(db, [UserRole.ADMIN])
        if err:
            return err
        data = request.get_json() or {}
        is_active = data.get("is_active", True)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"detail": "User not found"}), 404

        user.is_active = is_active
        user.updated_at = datetime.utcnow()

        audit = AuditLog(
            user_id=admin_user.id,
            username=admin_user.username,
            action="ACCOUNT_STATUS_CHANGE",
            entity_name="User",
            entity_id=str(user.id),
            details={"target_username": user.username, "is_active": is_active}
        )
        db.add(audit)
        db.commit()
        return jsonify({"message": f"User account {'enabled' if is_active else 'disabled'}", "user_id": user.id})
    finally:
        close_db(db)

# --- 2. COMPLAINT SUBMISSION & MANAGEMENT ---
@app.route("/api/complaints", methods=["POST"])
def submit_complaint():
    db = get_db()
    try:
        current_user = get_current_user_from_req(db)
        data = request.get_json() or {}
        title = data.get("title", "")
        description = data.get("description", "")
        customer_type = data.get("customer_type", "REGULAR")
        product_service = data.get("product_service", "")
        order_ref = data.get("order_ref")
        transaction_ref = data.get("transaction_ref")
        prev_complaint_ref = data.get("prev_complaint_ref")
        channel = data.get("channel", "WEB_FORM")
        preferred_contact = data.get("preferred_contact", "EMAIL")

        clean_title = sanitize_input(title)
        clean_desc = sanitize_input(description)

        if len(clean_desc) < 10:
            return jsonify({"detail": "Complaint description is too short. Please provide details."}), 400

        prompt_inj_flag = detect_prompt_injection(clean_desc) or detect_prompt_injection(clean_title)
        is_dup, dup_code = check_duplicate_complaint(db, clean_title, clean_desc)

        count = db.query(Complaint).count() + 1
        code = f"CMP-{2026000 + count}"

        cust_id = data.get("customer_id")
        if not cust_id:
            c_email = data.get("customer_email") or (current_user.email if current_user else "customer@gmail.com")
            cust = db.query(Customer).filter(Customer.email == c_email).first()
            if cust:
                cust_id = cust.id

        complaint = Complaint(
            complaint_code=code,
            title=clean_title,
            description=clean_desc,
            customer_id=cust_id,
            customer_type=customer_type,
            product_service=product_service,
            order_ref=order_ref,
            transaction_ref=transaction_ref,
            prev_complaint_ref=prev_complaint_ref,
            channel=channel,
            preferred_contact=preferred_contact,
            status=ComplaintStatus.NEW.value,
            is_duplicate=is_dup,
            duplicate_of_code=dup_code,
            prompt_injection_flag=prompt_inj_flag
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        create_or_update_sla(db, complaint, complaint.priority)

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

        return jsonify({
            "id": complaint.id,
            "complaint_code": complaint.complaint_code,
            "title": complaint.title,
            "description": complaint.description,
            "status": complaint.status,
            "submitted_at": complaint.submitted_at.isoformat(),
            "prompt_injection_flag": complaint.prompt_injection_flag,
            "is_duplicate": complaint.is_duplicate
        })
    finally:
        close_db(db)

@app.route("/api/complaints", methods=["GET"])
def list_complaints():
    db = get_db()
    try:
        current_user = get_current_user_from_req(db)
        status_filter = request.args.get("status_filter")
        search = request.args.get("search")

        query = db.query(Complaint)
        if current_user and current_user.role == UserRole.CUSTOMER.value:
            cust = db.query(Customer).filter(Customer.email == current_user.email).first()
            if cust:
                query = query.filter(Complaint.customer_id == cust.id)

        if status_filter:
            query = query.filter(Complaint.status == status_filter)
        if search:
            query = query.filter((Complaint.title.contains(search)) | (Complaint.description.contains(search)) | (Complaint.complaint_code.contains(search)))

        complaints = query.order_by(Complaint.id.desc()).all()
        res = []
        for c in complaints:
            comp_status = c.comparison.overall_status if c.comparison else "NOT ANALYZED"
            score = c.comparison.overall_verification_score if c.comparison else 0.0
            res.append({
                "id": c.id,
                "complaint_code": c.complaint_code,
                "title": c.title,
                "description": c.description,
                "customer_type": c.customer_type,
                "product_service": c.product_service,
                "order_ref": c.order_ref,
                "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
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
        return jsonify(res)
    finally:
        close_db(db)

@app.route("/api/complaints/<int:complaint_id>", methods=["GET"])
def get_complaint_details(complaint_id):
    db = get_db()
    try:
        user, err = require_auth(db)
        if err:
            return err
        c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not c:
            return jsonify({"detail": "Complaint not found"}), 404

        genai = c.genai_analysis
        py_val = c.python_validation
        comp = c.comparison
        sla = c.sla_record

        def to_dict_m(obj):
            if not obj:
                return None
            res = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.name)
                if isinstance(val, datetime):
                    val = val.isoformat()
                res[col.name] = val
            return res

        return jsonify({
            "complaint": to_dict_m(c),
            "genai_analysis": to_dict_m(genai),
            "python_validation": to_dict_m(py_val),
            "comparison": to_dict_m(comp),
            "manual_reviews": [to_dict_m(r) for r in c.manual_reviews],
            "sla": {
                "response_deadline": sla.response_deadline.isoformat() if sla and sla.response_deadline else None,
                "resolution_deadline": sla.resolution_deadline.isoformat() if sla and sla.resolution_deadline else None,
                "status": evaluate_sla_status(sla) if sla else "ON_TRACK"
            }
        })
    finally:
        close_db(db)

# --- 3. DUAL-PIPELINE AI ANALYSIS & GROUND-TRUTH ENGINE ---
@app.route("/api/complaints/<int:complaint_id>/analyze", methods=["POST"])
def analyze_complaint(complaint_id):
    db = get_db()
    try:
        user, err = require_auth(db)
        if err:
            return err

        c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not c:
            return jsonify({"detail": "Complaint not found"}), 404

        relevant_policies = retrieve_relevant_policies(db, c.description, top_k=3)
        genai_res = run_genai_analysis(c.complaint_code, c.title, c.description, relevant_policies)

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

        c.status = ComplaintStatus.ANALYZED.value
        c.priority = py_res.verified_priority
        c.urgency = py_res.verified_urgency
        c.sentiment = genai_res.sentiment

        if comp_res[0] in ["MISMATCH", "REVIEW REQUIRED"] or py_res.verified_escalation_required:
            c.status = ComplaintStatus.ESCALATED.value

        create_or_update_sla(db, c, c.priority)
        db.commit()

        return jsonify({
            "complaint_code": c.complaint_code,
            "genai_analysis": genai_res.dict(),
            "python_validation": py_res.dict(),
            "comparison_status": comp_res[0],
            "overall_verification_score": comp_res[8],
            "mismatches": [m.dict() for m in comp_res[9]]
        })
    finally:
        close_db(db)

# --- 4. MANUAL REVIEW QUEUE & ACTIONS ---
@app.route("/api/reviews", methods=["GET"])
def get_manual_review_queue():
    db = get_db()
    try:
        user, err = require_auth(db, [UserRole.REVIEWER, UserRole.MANAGER, UserRole.ADMIN])
        if err:
            return err
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
                "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
                "status": c.status,
                "genai_category": c.genai_analysis.category if c.genai_analysis else "N/A",
                "python_category": c.python_validation.verified_category if c.python_validation else "N/A",
                "overall_status": comp.overall_status,
                "overall_verification_score": comp.overall_verification_score,
                "mismatch_count": len(comp.mismatches or [])
            })
        return jsonify(queue)
    finally:
        close_db(db)

@app.route("/api/complaints/<int:complaint_id>/review", methods=["POST"])
def submit_manual_review(complaint_id):
    db = get_db()
    try:
        user, err = require_auth(db, [UserRole.REVIEWER, UserRole.MANAGER, UserRole.ADMIN])
        if err:
            return err
        c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not c:
            return jsonify({"detail": "Complaint not found"}), 404

        data = request.get_json() or {}
        reviewer_action = data.get("reviewer_action", "APPROVE")
        modified_category = data.get("modified_category")
        modified_department = data.get("modified_department")
        modified_escalation_level = data.get("modified_escalation_level")
        reviewer_comments = data.get("reviewer_comments", "")

        review = ManualReview(
            complaint_id=c.id,
            reviewer_id=user.id,
            review_reason="Manual override by authorized reviewer",
            reviewer_action=reviewer_action,
            modified_category=modified_category,
            modified_department=modified_department,
            modified_escalation_level=modified_escalation_level,
            reviewer_comments=reviewer_comments
        )
        db.add(review)

        if reviewer_action == "APPROVE":
            c.status = ComplaintStatus.IN_PROGRESS.value
        elif reviewer_action == "REJECT":
            c.status = ComplaintStatus.CLOSED.value
        elif reviewer_action == "ESCALATE":
            c.status = ComplaintStatus.ESCALATED.value

        db.commit()
        return jsonify({"message": "Review decision recorded successfully", "status": c.status})
    finally:
        close_db(db)

# --- 5. KNOWLEDGE BASE & POLICY MANAGEMENT ---
@app.route("/api/policies", methods=["GET"])
def list_policies():
    db = get_db()
    try:
        policies = db.query(Policy).all()
        return jsonify([{
            "id": p.id,
            "doc_id": p.doc_id,
            "title": p.title,
            "category": p.category,
            "status": p.status,
            "version": p.version,
            "effective_date": p.effective_date.isoformat() if p.effective_date else None,
            "file_type": p.file_type,
            "source_reference": p.source_reference,
            "content_snippet": (p.content[:200] + "...") if p.content else ""
        } for p in policies])
    finally:
        close_db(db)

@app.route("/api/policies/upload", methods=["POST"])
def upload_policy_document():
    db = get_db()
    try:
        user, err = require_auth(db, [UserRole.ADMIN])
        if err:
            return err
        title = request.form.get("title", "Untitled Policy")
        category = request.form.get("category", "General Policy")
        version = request.form.get("version", "1.0")
        file = request.files.get("file")

        if not file:
            return jsonify({"detail": "File is required"}), 400

        os.makedirs("./data/uploads", exist_ok=True)
        file_path = f"./data/uploads/{file.filename}"
        file.save(file_path)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".pdf":
            pages = parse_pdf(file_path)
            content = "\n".join([p["text"] for p in pages])
        elif ext in [".docx", ".doc"]:
            sections = parse_docx(file_path)
            content = "\n".join([s["text"] for s in sections])
        else:
            content = parse_txt(file_path)

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
        return jsonify({"message": "Policy uploaded and chunked successfully", "doc_id": doc_id, "chunk_count": len(chunks)})
    finally:
        close_db(db)

# --- 6. RULE MATRIX MANAGEMENT ---
@app.route("/api/rules", methods=["GET"])
def get_rule_matrix():
    db = get_db()
    try:
        rules = db.query(RuleMatrix).all()
        return jsonify([{
            "id": r.id,
            "rule_id": r.rule_id,
            "title": r.title,
            "category": r.category,
            "subcategory": r.subcategory,
            "trigger_condition": r.trigger_condition,
            "mandated_department": r.mandated_department,
            "mandated_urgency": r.mandated_urgency,
            "mandated_priority": r.mandated_priority,
            "refund_eligible": r.refund_eligible,
            "replacement_eligible": r.replacement_eligible,
            "compensation_eligible": r.compensation_eligible,
            "policy_doc_ref": r.policy_doc_ref,
            "is_active": r.is_active
        } for r in rules])
    finally:
        close_db(db)

# --- 7. PROMPT MANAGEMENT ---
@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    db = get_db()
    try:
        prompts = db.query(PromptTemplate).all()
        return jsonify([{
            "id": p.id,
            "template_name": p.template_name,
            "version": p.version,
            "system_prompt": p.system_prompt,
            "user_prompt_template": p.user_prompt_template,
            "json_schema_definition": p.json_schema_definition,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in prompts])
    finally:
        close_db(db)

# --- 8. ANALYTICS & DASHBOARDS ---
@app.route("/api/analytics/summary", methods=["GET"])
def get_analytics_summary():
    db = get_db()
    try:
        total = db.query(Complaint).count()
        analyzed = db.query(Complaint).filter(Complaint.status == "ANALYZED").count()
        escalated = db.query(Complaint).filter(Complaint.status == "ESCALATED").count()
        resolved = db.query(Complaint).filter(Complaint.status == "RESOLVED").count()

        matches = db.query(Comparison).filter(Comparison.overall_status == "MATCH").count()
        mismatches = db.query(Comparison).filter(Comparison.overall_status == "MISMATCH").count()
        reviews = db.query(Comparison).filter(Comparison.overall_status == "REVIEW REQUIRED").count()

        p0 = db.query(Complaint).filter(Complaint.priority.contains("P0")).count()
        p1 = db.query(Complaint).filter(Complaint.priority.contains("P1")).count()
        p2 = db.query(Complaint).filter(Complaint.priority.contains("P2")).count()
        p3 = db.query(Complaint).filter(Complaint.priority.contains("P3")).count()

        return jsonify({
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
        })
    finally:
        close_db(db)

# --- 9. REPORTS & EXPORTS ---
@app.route("/api/reports/csv", methods=["GET"])
def download_csv_report():
    db = get_db()
    try:
        csv_data = generate_csv_complaints_report(db)
        response = make_response(csv_data)
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = "attachment; filename=SupportNova_Complaints_Report.csv"
        return response
    finally:
        close_db(db)

@app.route("/api/reports/100-case-evaluation", methods=["GET"])
def get_100_case_report():
    db = get_db()
    try:
        res = generate_100_case_comparison_report(db)
        return jsonify(res)
    finally:
        close_db(db)

# --- 10. AUDIT LOGS ---
@app.route("/api/audit-logs", methods=["GET"])
def list_audit_logs():
    db = get_db()
    try:
        user, err = require_auth(db, [UserRole.ADMIN])
        if err:
            return err
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
        return jsonify([{
            "id": l.id,
            "user_id": l.user_id,
            "username": l.username,
            "complaint_code": l.complaint_code,
            "action": l.action,
            "entity_name": l.entity_name,
            "entity_id": l.entity_id,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        } for l in logs])
    finally:
        close_db(db)

# Initialize database schema and seed data on startup
with app.app_context():
    Base.metadata.create_all(bind=engine)
    seed_database()

if __name__ == "__main__":
    print("Starting SupportNova Flask Backend Server on port 8000...")
    app.run(host="0.0.0.0", port=8000, debug=True)
