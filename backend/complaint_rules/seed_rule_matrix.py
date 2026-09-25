"""
Seed script for SupportNova Complaint Resolution Rule Matrix.
Generates >= 100 structured business rules across all 10 categories and 33 subcategories
for NexaLink Communications, with >= 30 escalation_required=True rules and SRS tricky cases.
Exports data to config/rule_matrix_seed.json and populates database/store.
"""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CATEGORIES_FILE = CONFIG_DIR / "categories.json"
DEPARTMENTS_FILE = CONFIG_DIR / "departments.json"
SEED_OUTPUT_FILE = CONFIG_DIR / "rule_matrix_seed.json"


def load_json(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_seed_rules() -> List[Dict[str, Any]]:
    categories_data = load_json(CATEGORIES_FILE)
    departments_data = load_json(DEPARTMENTS_FILE)

    categories = categories_data.get("categories", [])
    dept_map = {d["id"]: d["name"] for d in departments_data.get("departments", [])}

    rules: List[Dict[str, Any]] = []
    rule_counter = 1

    # Mapping policy references
    policy_refs = {
        "CAT-001": "KB-DOC-1002",  # Billing SOP
        "CAT-002": "KB-DOC-1003",  # Network SLA
        "CAT-003": "KB-DOC-1004",  # Complaint SOP
        "CAT-004": "KB-DOC-1004",
        "CAT-005": "KB-DOC-1003",
        "CAT-006": "KB-DOC-1001",  # Refund policy
        "CAT-007": "KB-DOC-1004",
        "CAT-008": "KB-DOC-1004",
        "CAT-009": "KB-DOC-1004",
        "CAT-010": "KB-DOC-1003",
    }

    # Generate 3-4 rules per subcategory (33 subcategories * 3.2 ~ 105 total rules)
    for cat in categories:
        cat_code = cat["code"]
        cat_name = cat["name"]
        primary_dept_id = cat["responsible_department_id"]
        primary_dept_name = dept_map.get(primary_dept_id, "Customer Account Services")
        pol_id = policy_refs.get(cat["id"], "KB-DOC-1001")

        for subcat in cat.get("subcategories", []):
            subcat_code = subcat["code"]
            subcat_name = subcat["name"]

            # Standard Rule 1: Normal Tier 1 / Low-Medium Priority Case
            rid1 = f"RULE-{rule_counter:04d}"
            rule_counter += 1
            rules.append({
                "rule_id": rid1,
                "category": cat_name,
                "subcategory": subcat_name,
                "conditions": {
                    "customer_tier": "standard",
                    "dispute_amount_max": 100.0,
                    "business_risk_level": "low"
                },
                "department": primary_dept_name,
                "supporting_departments": [],
                "urgency": "Low",
                "priority": "Medium",
                "policy_id": pol_id,
                "escalation_required": False,
                "escalation_level": None,
                "required_actions": [f"Verify {subcat_name} history", "Issue standard explanation or waiver within $50 limit"],
                "prohibited_actions": ["Do not promise unapproved goodwill compensation exceeding $50"],
                "follow_up_required": False,
                "is_active": True,
                "created_by": "admin@nexalink.com",
                "created_at": "2026-01-15T08:00:00Z",
                "updated_at": "2026-01-15T08:00:00Z"
            })

            # Standard Rule 2: Premium / High Priority Case
            rid2 = f"RULE-{rule_counter:04d}"
            rule_counter += 1
            rules.append({
                "rule_id": rid2,
                "category": cat_name,
                "subcategory": subcat_name,
                "conditions": {
                    "customer_tier": "vip",
                    "dispute_amount_min": 100.0,
                    "dispute_amount_max": 500.0
                },
                "department": primary_dept_name,
                "supporting_departments": ["Billing & Revenue Assurance"],
                "urgency": "Medium",
                "priority": "High",
                "policy_id": pol_id,
                "escalation_required": False,
                "escalation_level": None,
                "required_actions": ["Apply priority queue routing", f"Review VIP contract terms for {subcat_name}"],
                "prohibited_actions": ["Do not disconnect service during active dispute"],
                "follow_up_required": True,
                "is_active": True,
                "created_by": "admin@nexalink.com",
                "created_at": "2026-01-15T08:30:00Z",
                "updated_at": "2026-01-15T08:30:00Z"
            })

            # Escalation Rule 3: High-Value / Mandatory Escalation Case
            rid3 = f"RULE-{rule_counter:04d}"
            rule_counter += 1
            is_high_risk_cat = cat_code in ["SECURITY", "COMPLIANCE", "NETWORK", "INSTALLATION"]

            rules.append({
                "rule_id": rid3,
                "category": cat_name,
                "subcategory": subcat_name,
                "conditions": {
                    "repeat_complaints_min": 3,
                    "unresolved_days_min": 5
                },
                "department": primary_dept_name if not is_high_risk_cat else "Executive Escalations & Customer Relations",
                "supporting_departments": ["Regulatory Affairs & Legal Compliance", "Executive Escalations & Customer Relations"],
                "urgency": "High" if not is_high_risk_cat else "Critical",
                "priority": "High" if not is_high_risk_cat else "Urgent",
                "policy_id": pol_id,
                "escalation_required": True,
                "escalation_level": "Tier 2 Manager Review",
                "required_actions": ["Freeze automated billing action", "Assign dedicated escalation specialist", "Outbound phone follow-up"],
                "prohibited_actions": ["Do not send automated rejection letter", "Do not transfer caller between general queues"],
                "follow_up_required": True,
                "is_active": True,
                "created_by": "admin@nexalink.com",
                "created_at": "2026-01-15T09:00:00Z",
                "updated_at": "2026-01-15T09:00:00Z"
            })

    # ── Explicit Tricky Case Rules for SRS Acceptance Criteria ─────────────────

    # Tricky Rule A: Calm tone + Safety Keyword -> Mandatory Critical Escalation
    rules.append({
        "rule_id": "RULE-0101",
        "category": "Device & Equipment",
        "subcategory": "Router / Mesh Node Malfunction",
        "conditions": {
            "contains_safety_keyword": True,
            "sentiment_score_min": 0.5  # Calm, polite, or neutral tone
        },
        "department": "Field Operations & Installation Services",
        "supporting_departments": ["Regulatory Affairs & Legal Compliance", "Device & Warranty Services"],
        "urgency": "Critical",
        "priority": "Urgent",
        "policy_id": "KB-DOC-1004",
        "escalation_required": True,
        "escalation_level": "Safety & Hazards Escalation Desk",
        "required_actions": [
            "Immediately flag as hazardous equipment incident",
            "Dispatch emergency technician for device recall and safety audit",
            "Notify Product Safety Risk Officer within 2 hours"
        ],
        "prohibited_actions": [
            "Do not deprioritize or delay dispatch based on polite or calm customer phrasing",
            "Do not instruct customer to continue using overheating hardware"
        ],
        "follow_up_required": True,
        "is_active": True,
        "created_by": "admin@nexalink.com",
        "created_at": "2026-02-01T10:00:00Z",
        "updated_at": "2026-02-01T10:00:00Z"
    })

    # Tricky Rule B: Angry tone + Low Business Risk -> Low/Medium Priority
    rules.append({
        "rule_id": "RULE-0102",
        "category": "Billing & Payments",
        "subcategory": "Promotional Discount Not Applied",
        "conditions": {
            "contains_safety_keyword": False,
            "business_risk_level": "low",
            "dispute_amount_max": 25.0
        },
        "department": "Billing & Revenue Assurance",
        "supporting_departments": [],
        "urgency": "Low",
        "priority": "Medium",
        "policy_id": "KB-DOC-1002",
        "escalation_required": False,
        "escalation_level": None,
        "required_actions": [
            "Verify promo code validity on account",
            "Issue routine one-time bill credit up to $25",
            "Send polite written confirmation email"
        ],
        "prohibited_actions": [
            "Do not escalate to executive care solely due to hostile language or profanity",
            "Do not issue unverified credits above policy threshold"
        ],
        "follow_up_required": False,
        "is_active": True,
        "created_by": "admin@nexalink.com",
        "created_at": "2026-02-01T10:30:00Z",
        "updated_at": "2026-02-01T10:30:00Z"
    })

    # Additional Mandatory Escalation Triggers (Legal, Security, Privacy, Outage)
    escalation_triggers = [
        {
            "rule_id": "RULE-0103",
            "category": "Account Security & Fraud",
            "subcategory": "Unauthorized SIM Swap / Port-Out",
            "conditions": {"security_incident_type": "sim_swap"},
            "department": "Account Security & Fraud Prevention",
            "supporting_departments": ["Regulatory Affairs & Legal Compliance"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1003",
            "escalation_required": True,
            "escalation_level": "Tier 3 Fraud Security Desk",
            "required_actions": ["Lock account credentials immediately", "Verify government ID", "Notify Fraud Response Lead"],
            "prohibited_actions": ["Do not unlock account without dual-factor identity verification"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@nexalink.com",
            "created_at": "2026-02-02T09:00:00Z",
            "updated_at": "2026-02-02T09:00:00Z"
        },
        {
            "rule_id": "RULE-0104",
            "category": "Regulatory & Compliance",
            "subcategory": "FCC / State Regulator Referenced Complaint",
            "conditions": {"legal_regulatory_threat": True},
            "department": "Regulatory Affairs & Legal Compliance",
            "supporting_departments": ["Executive Escalations & Customer Relations"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1003",
            "escalation_required": True,
            "escalation_level": "Chief Compliance Officer Review",
            "required_actions": ["Route directly to Legal Compliance desk", "Preserve all account logs and recordings"],
            "prohibited_actions": ["Do not attempt informal settlement without Legal sign-off"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@nexalink.com",
            "created_at": "2026-02-02T09:30:00Z",
            "updated_at": "2026-02-02T09:30:00Z"
        },
        {
            "rule_id": "RULE-0105",
            "category": "Network & Connectivity",
            "subcategory": "No Signal / Complete Outage",
            "conditions": {"affected_subscribers_min": 100},
            "department": "Network Operations & Engineering",
            "supporting_departments": ["Field Operations & Installation Services"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1003",
            "escalation_required": True,
            "escalation_level": "Major Incident Response Command",
            "required_actions": ["Trigger emergency network outage protocol", "Broadcast status to web banner"],
            "prohibited_actions": ["Do not close individual trouble tickets until trunk node is restored"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@nexalink.com",
            "created_at": "2026-02-02T10:00:00Z",
            "updated_at": "2026-02-02T10:00:00Z"
        }
    ]

    rules.extend(escalation_triggers)

    return rules


def main():
    rules = generate_seed_rules()
    total_count = len(rules)
    escalation_count = sum(1 for r in rules if r.get("escalation_required"))

    print(f"Generated {total_count} total rules.")
    print(f"Escalation required rules: {escalation_count}")

    # Export to config/rule_matrix_seed.json
    with open(SEED_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "config_version": "2.0",
            "last_updated": "2026-09-25",
            "total_rules": total_count,
            "escalation_required_count": escalation_count,
            "rules": rules
        }, f, indent=2)

    print(f"Exported seed data to {SEED_OUTPUT_FILE}")

    # Seed database table rule_matrix if SQLAlchemy DB available
    try:
        from backend.database.db import init_db, SessionLocal, HAS_SQLALCHEMY
        from backend.database.models import RuleMatrixModel, KnowledgeDocumentModel
        if HAS_SQLALCHEMY and SessionLocal:
            init_db()
            db = SessionLocal()
            try:
                # Collect unique policy IDs referenced by rules
                unique_pols = {r.get("policy_id") for r in rules if r.get("policy_id")}
                for pol_id in unique_pols:
                    kb_doc = db.query(KnowledgeDocumentModel).filter_by(document_id=pol_id).first()
                    if not kb_doc:
                        db.add(KnowledgeDocumentModel(
                            document_id=pol_id,
                            title=f"Seed Policy Document ({pol_id})",
                            category="policy",
                            version="1.0",
                            status="Active",
                            effective_date="2026-01-01",
                            file_name=f"{pol_id}.pdf",
                            file_path=f"sample_documents/{pol_id}.pdf",
                            content_hash=f"hash_seed_{pol_id}"
                        ))
                db.commit()

                # Upsert rules into database table rule_matrix
                db_rule_count = 0
                for r in rules:
                    existing = db.query(RuleMatrixModel).filter_by(rule_id=r["rule_id"]).first()
                    if not existing:
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
                            created_by=r.get("created_by", "admin@nexalink.com"),
                        )
                        db.add(db_rule)
                        db_rule_count += 1
                db.commit()
                print(f"Populated database table 'rule_matrix' with {db_rule_count} new entries.")
            except Exception as e:
                db.rollback()
                print(f"Database seed note: {e}")
            finally:
                db.close()
    except Exception as err:
        print(f"Database seed skipped: {err}")


if __name__ == "__main__":
    main()

