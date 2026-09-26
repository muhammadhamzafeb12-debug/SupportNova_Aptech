"""
SupportNova Production Database Seeder Script
Populates database tables and in-memory stores with:
1. 5 Core Role Test Accounts (Customer, Agent, Reviewer, Manager, Administrator)
2. Organization Config & 21 KB Documents + Semantic Chunks
3. 100+ Rule Matrix Engine Business Rules
4. Representative Sample Complaints Dataset
"""
import sys
import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database.db import init_db, SessionLocal, HAS_SQLALCHEMY
from backend.database.models import (
    UserModel,
    KnowledgeDocumentModel,
    KBChunkModel,
    RuleMatrixModel,
    ComplaintModel
)
from backend.security.auth import get_hash, MOCK_USERS
from backend.security.jwt_auth import USER_DB
from backend.src.store import (
    RULE_MATRIX_STORE,
    KNOWLEDGE_BASE_STORE,
    KB_CHUNKS_STORE,
    COMPLAINTS_STORE
)
from backend.complaint_rules.seed_rule_matrix import generate_seed_rules
from scripts.build_and_upload_kb import DOCUMENTS_SPEC, SAMPLE_DOCS_DIR
from backend.document_processing.pipeline import process_document_pipeline

def seed_users(db_session):
    print("--- Seeding Test Role Accounts ---")
    test_accounts = [
        {"email": "customer@velvocart.com", "username": "customer", "name": "Sarah Jenkins", "role": "Customer", "pass_hashes": [get_hash("password123"), get_hash("customer123")]},
        {"email": "agent@velvocart.com", "username": "agent", "name": "Marcus Vance", "role": "Agent", "pass_hashes": [get_hash("password123"), get_hash("agent123")]},
        {"email": "reviewer@velvocart.com", "username": "reviewer", "name": "Elena Rostova", "role": "Reviewer", "pass_hashes": [get_hash("password123"), get_hash("reviewer123")]},
        {"email": "manager@velvocart.com", "username": "manager", "name": "David Sterling", "role": "Manager", "pass_hashes": [get_hash("password123"), get_hash("manager123")]},
        {"email": "admin@velvocart.com", "username": "admin", "name": "System Administrator", "role": "Admin", "pass_hashes": [get_hash("password123"), get_hash("admin123")]},
    ]

    for acc in test_accounts:
        # Populate MOCK_USERS and USER_DB with email & short username aliases
        USER_DB[acc["email"]] = {
            "username": acc["email"],
            "full_name": acc["name"],
            "role": acc["role"],
            "password_hash": acc["pass_hashes"][0]
        }
        USER_DB[acc["username"]] = {
            "username": acc["email"],
            "full_name": acc["name"],
            "role": acc["role"],
            "password_hash": acc["pass_hashes"][1]
        }
        MOCK_USERS[acc["email"]] = USER_DB[acc["email"]]
        MOCK_USERS[acc["username"]] = USER_DB[acc["username"]]

        if db_session:
            existing = db_session.query(UserModel).filter(UserModel.email == acc["email"]).first()
            if not existing:
                user_obj = UserModel(
                    email=acc["email"],
                    full_name=acc["name"],
                    role=acc["role"],
                    hashed_password=acc["pass_hashes"][0],
                    created_at=datetime.utcnow()
                )
                db_session.add(user_obj)

    if db_session:
        db_session.commit()
    print("Successfully seeded 5 test role accounts across email and username aliases.")

def seed_kb(db_session):
    print("--- Seeding Knowledge Base Documents & Chunks ---")
    SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_BASE_STORE.clear()
    KB_CHUNKS_STORE.clear()

    if db_session:
        db_session.query(KBChunkModel).delete()
        db_session.query(KnowledgeDocumentModel).delete()
        db_session.commit()

    for doc in DOCUMENTS_SPEC:
        file_path = SAMPLE_DOCS_DIR / doc["filename"]
        file_path.write_text(doc["content"], encoding="utf-8")
        str_file_path = str(file_path)

        kb_rec = {
            "document_id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "version": doc["version"],
            "status": doc["status"],
            "effective_date": doc["effective_date"],
            "file_name": doc["filename"],
            "file_path": str_file_path,
            "content_hash": hashlib.sha256(doc["content"].encode('utf-8')).hexdigest(),
            "content": doc["content"],
            "parsing_status": "pending",
            "parsing_error": None,
            "chunk_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        KNOWLEDGE_BASE_STORE.append(kb_rec)

        if db_session:
            db_doc = KnowledgeDocumentModel(
                document_id=doc["id"],
                title=doc["title"],
                category=doc["category"],
                version=doc["version"],
                status=doc["status"],
                effective_date=doc["effective_date"],
                file_name=doc["filename"],
                file_path=str_file_path,
                content_hash=kb_rec["content_hash"],
                content=doc["content"],
                parsing_status="completed"
            )
            db_session.add(db_doc)

        process_document_pipeline(
            document_id=doc["id"],
            file_path=str_file_path,
            version=doc["version"],
            kb_store=KNOWLEDGE_BASE_STORE,
            chunks_store=KB_CHUNKS_STORE
        )

    if db_session:
        db_session.commit()
        for chk in KB_CHUNKS_STORE:
            db_chk = KBChunkModel(
                chunk_id=chk.get("chunk_id", f"chk_{chk.get('document_id')}_{chk.get('section')}"),
                document_id=chk.get("document_id"),
                section=chk.get("section"),
                heading=chk.get("heading"),
                version=chk.get("version", "1.0"),
                text=chk.get("text", "")
            )
            db_session.add(db_chk)
        db_session.commit()

    print(f"Successfully seeded {len(KNOWLEDGE_BASE_STORE)} KB documents & {len(KB_CHUNKS_STORE)} semantic chunks.")

def seed_rules(db_session):
    print("--- Seeding Rule Matrix Business Rules ---")
    rules = generate_seed_rules()
    RULE_MATRIX_STORE.clear()
    RULE_MATRIX_STORE.extend(rules)

    if db_session:
        db_session.query(RuleMatrixModel).delete()
        db_session.commit()
        for r in rules:
            db_rule = RuleMatrixModel(
                rule_id=r["rule_id"],
                category=r["category"],
                subcategory=r["subcategory"],
                conditions=r["conditions"],
                department=r["department"],
                supporting_departments=r.get("supporting_departments", []),
                urgency=r["urgency"],
                priority=r["priority"],
                policy_id=r["policy_id"],
                escalation_required=r.get("escalation_required", False),
                escalation_level=r.get("escalation_level"),
                required_actions=r.get("required_actions", []),
                prohibited_actions=r.get("prohibited_actions", []),
                follow_up_required=r.get("follow_up_required", False),
                is_active=r.get("is_active", True),
                created_by=r.get("created_by", "admin@velvocart.com")
            )
            db_session.add(db_rule)
        db_session.commit()
    print(f"Successfully seeded {len(rules)} Rule Matrix rules.")

def seed_complaints(db_session):
    print("--- Seeding Representative Sample Complaints Dataset ---")
    dataset_file = PROJECT_ROOT / "sample_complaints" / "complaints_dataset.json"
    if not dataset_file.exists():
        print(f"Dataset file {dataset_file} not found, skipping complaints dataset seed.")
        return

    try:
        with open(dataset_file, "r", encoding="utf-8") as f:
            complaints_data = json.load(f)
    except Exception as e:
        print(f"Error reading dataset: {e}")
        return

    if isinstance(complaints_data, dict):
        complaints_list = complaints_data.get("complaints", [])
    elif isinstance(complaints_data, list):
        complaints_list = complaints_data
    else:
        complaints_list = []

    if db_session:
        db_session.query(ComplaintModel).delete()
        db_session.commit()

    sample_seed = complaints_list[:25]
    seeded_count = 0

    for idx, c in enumerate(sample_seed, 1):
        c_num = c.get("complaint_number") or f"CMP-2026-{1000 + idx}"
        c_obj = {
            "id": idx,
            "complaint_number": c_num,
            "customer_email": c.get("customer_email", "customer@velvocart.com"),
            "customer_name": c.get("customer_name", "Sarah Jenkins"),
            "account_number": c.get("account_number", f"ACC-{994800 + idx}"),
            "title": c.get("title", f"Complaint {c_num}"),
            "category": c.get("category", "Order & Delivery"),
            "sub_category": c.get("sub_category") or c.get("subcategory") or "Delayed Delivery",
            "description": c.get("description", "Sample complaint description"),
            "status": c.get("status", "In Progress"),
            "priority": c.get("priority", "Medium"),
            "assigned_department": c.get("assigned_department", "Order Fulfillment & Logistics"),
            "assigned_agent": c.get("assigned_agent", "Marcus Vance"),
            "sentiment_score": c.get("sentiment_score", 0.5),
            "genai_summary": c.get("genai_summary", "Summary of customer complaint."),
            "genai_suggested_response": c.get("genai_suggested_response", "Thank you for contacting VelvoCart support."),
            "genai_confidence": c.get("genai_confidence", 0.90),
            "python_validation_passed": c.get("python_validation_passed", True),
            "python_validation_flags": c.get("python_validation_flags", []),
            "has_hallucination": c.get("has_hallucination", False),
            "hallucination_details": c.get("hallucination_details", None),
            "requested_credit": c.get("requested_credit", 0.0),
            "approved_credit": c.get("approved_credit", 0.0),
            "created_at": c.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": c.get("updated_at", datetime.utcnow().isoformat())
        }
        COMPLAINTS_STORE.append(c_obj)

        if db_session:
            db_c = ComplaintModel(
                complaint_number=c_obj["complaint_number"],
                customer_email=c_obj["customer_email"],
                customer_name=c_obj["customer_name"],
                account_number=c_obj["account_number"],
                title=c_obj["title"],
                category=c_obj["category"],
                sub_category=c_obj["sub_category"],
                description=c_obj["description"],
                status=c_obj["status"],
                priority=c_obj["priority"],
                assigned_department=c_obj["assigned_department"],
                assigned_agent=c_obj["assigned_agent"],
                sentiment_score=c_obj["sentiment_score"],
                genai_summary=c_obj["genai_summary"],
                genai_suggested_response=c_obj["genai_suggested_response"],
                genai_confidence=c_obj["genai_confidence"],
                python_validation_passed=c_obj["python_validation_passed"],
                python_validation_flags=c_obj["python_validation_flags"],
                has_hallucination=c_obj["has_hallucination"],
                hallucination_details=c_obj["hallucination_details"],
                requested_credit=c_obj["requested_credit"],
                approved_credit=c_obj["approved_credit"]
            )
            db_session.add(db_c)
        seeded_count += 1

    if db_session:
        db_session.commit()
    print(f"Successfully seeded {seeded_count} sample complaints into database & store.")

def main():
    print("=========================================================")
    print("SupportNova Production Database Seeder Starting...")
    print("=========================================================")
    init_db()

    db_session = None
    if HAS_SQLALCHEMY and SessionLocal:
        try:
            db_session = SessionLocal()
        except Exception as e:
            print(f"SQLAlchemy Session creation note: {e}")

    try:
        seed_users(db_session)
        seed_kb(db_session)
        seed_rules(db_session)
        seed_complaints(db_session)
        print("=========================================================")
        print("SupportNova Seeding Completed Successfully!")
        print("=========================================================")
    finally:
        if db_session:
            db_session.close()

if __name__ == "__main__":
    main()
