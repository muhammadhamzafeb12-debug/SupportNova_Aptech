"""
Seed script for SupportNova Complaint Resolution Rule Matrix — E-Commerce Domain (VelvoCart).
Generates >= 100 structured business rules across all 10 e-commerce categories and 38 subcategories
for VelvoCart Online Marketplace, with >= 30 escalation_required=True rules and SRS tricky cases.
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

    # Mapping category to KB Policy Docs
    policy_refs = {
        "CAT-001": "KB-DOC-1003",  # Delivery Policy
        "CAT-002": "KB-DOC-1005",  # Billing Policy
        "CAT-003": "KB-DOC-1001",  # Return Policy
        "CAT-004": "KB-DOC-1010",  # Quality / Protection Plan
        "CAT-005": "KB-DOC-1012",  # Complaint SOP
        "CAT-006": "KB-DOC-1008",  # Fraud & Security Policy
        "CAT-007": "KB-DOC-1007",  # Marketplace Seller Policy
        "CAT-008": "KB-DOC-1012",  # Support Care SOP
        "CAT-009": "KB-DOC-1005",  # Billing & Promo Policy
        "CAT-010": "KB-DOC-1009",  # Data Privacy Policy
    }

    # Generate 3 rules per subcategory (38 subcategories * 3 = 114 base rules)
    for cat in categories:
        cat_code = cat["code"]
        cat_name = cat["name"]
        primary_dept_id = cat["responsible_department_id"]
        primary_dept_name = dept_map.get(primary_dept_id, "Account Management & Customer Care")
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
                "required_actions": [f"Verify {subcat_name} order record", "Issue standard goodwill credit or replacement within $50 limit"],
                "prohibited_actions": ["Do not promise unapproved goodwill compensation exceeding $50"],
                "follow_up_required": False,
                "is_active": True,
                "created_by": "admin@velvocart.com",
                "created_at": "2026-01-15T08:00:00Z",
                "updated_at": "2026-01-15T08:00:00Z"
            })

            # Standard Rule 2: Prime / High Priority Case
            rid2 = f"RULE-{rule_counter:04d}"
            rule_counter += 1
            rules.append({
                "rule_id": rid2,
                "category": cat_name,
                "subcategory": subcat_name,
                "conditions": {
                    "customer_tier": "prime",
                    "dispute_amount_min": 100.0,
                    "dispute_amount_max": 500.0
                },
                "department": primary_dept_name,
                "supporting_departments": ["Billing & Payment Operations"],
                "urgency": "Medium",
                "priority": "High",
                "policy_id": pol_id,
                "escalation_required": False,
                "escalation_level": None,
                "required_actions": ["Apply VelvoCart Prime priority queue routing", f"Review purchase history for {subcat_name}"],
                "prohibited_actions": ["Do not cancel active order without customer authorization"],
                "follow_up_required": True,
                "is_active": True,
                "created_by": "admin@velvocart.com",
                "created_at": "2026-01-15T08:30:00Z",
                "updated_at": "2026-01-15T08:30:00Z"
            })

            # Escalation Rule 3: High-Value / Mandatory Escalation Case
            rid3 = f"RULE-{rule_counter:04d}"
            rule_counter += 1
            is_high_risk_cat = cat_code in ["SECURITY", "COMPLIANCE", "PRODUCT", "MARKETPLACE"]

            rules.append({
                "rule_id": rid3,
                "category": cat_name,
                "subcategory": subcat_name,
                "conditions": {
                    "repeat_complaints_min": 3,
                    "unresolved_days_min": 5
                },
                "department": primary_dept_name if not is_high_risk_cat else "Executive Escalations & Customer Relations",
                "supporting_departments": ["Compliance & Legal Affairs", "Executive Escalations & Customer Relations"],
                "urgency": "High" if not is_high_risk_cat else "Critical",
                "priority": "High" if not is_high_risk_cat else "Urgent",
                "policy_id": pol_id,
                "escalation_required": True,
                "escalation_level": "Tier 2 Operations Manager Review",
                "required_actions": ["Freeze automated merchant payment payout", "Assign dedicated escalation specialist", "Outbound phone follow-up"],
                "prohibited_actions": ["Do not send automated rejection letter", "Do not transfer buyer between general support queues"],
                "follow_up_required": True,
                "is_active": True,
                "created_by": "admin@velvocart.com",
                "created_at": "2026-01-15T09:00:00Z",
                "updated_at": "2026-01-15T09:00:00Z"
            })

    # ── SRS Explicit Tricky Priority Cases ─────────────────────────────────────

    # Tricky Rule A: Calm tone + Safety/Counterfeit Hazard -> Mandatory Critical Escalation
    rules.append({
        "rule_id": "RULE-0120",
        "category": "Product Quality & Authenticity",
        "subcategory": "Defective or Malfunctioning Product",
        "conditions": {
            "contains_safety_keyword": True,
            "sentiment_score_min": 0.5  # Calm, polite, or neutral tone
        },
        "department": "Trust & Safety (Fraud & Security)",
        "supporting_departments": ["Compliance & Legal Affairs", "Product Quality & Vendor Assurance"],
        "urgency": "Critical",
        "priority": "Urgent",
        "policy_id": "KB-DOC-1010",
        "escalation_required": True,
        "escalation_level": "Product Safety & Risk Hazard Desk",
        "required_actions": [
            "Immediately flag listing for product safety hazard audit",
            "Quarantine warehouse inventory batch",
            "Notify Product Safety Risk Officer within 2 hours"
        ],
        "prohibited_actions": [
            "Do not deprioritize or delay dispatch based on polite or calm customer phrasing",
            "Do not instruct customer to continue using dangerous hardware"
        ],
        "follow_up_required": True,
        "is_active": True,
        "created_by": "admin@velvocart.com",
        "created_at": "2026-02-01T10:00:00Z",
        "updated_at": "2026-02-01T10:00:00Z"
    })

    # Tricky Rule B: Angry tone + Low Business Risk -> Low/Medium Priority
    rules.append({
        "rule_id": "RULE-0121",
        "category": "Promotions & Pricing",
        "subcategory": "Promo Code / Discount Rejected",
        "conditions": {
            "contains_safety_keyword": False,
            "business_risk_level": "low",
            "dispute_amount_max": 10.0
        },
        "department": "Billing & Payment Operations",
        "supporting_departments": [],
        "urgency": "Low",
        "priority": "Medium",
        "policy_id": "KB-DOC-1005",
        "escalation_required": False,
        "escalation_level": None,
        "required_actions": [
            "Verify promo code eligibility on order",
            "Issue routine one-time wallet credit up to $10",
            "Send polite confirmation email"
        ],
        "prohibited_actions": [
            "Do not escalate to executive care solely due to hostile language or profanity",
            "Do not issue unverified credits above policy threshold"
        ],
        "follow_up_required": False,
        "is_active": True,
        "created_by": "admin@velvocart.com",
        "created_at": "2026-02-01T10:30:00Z",
        "updated_at": "2026-02-01T10:30:00Z"
    })

    # Additional Mandatory Escalation Triggers (Security, Legal, Fake Sellers)
    escalation_triggers = [
        {
            "rule_id": "RULE-0122",
            "category": "Account Security & Fraud",
            "subcategory": "Account Takeover Suspected",
            "conditions": {"security_incident_type": "account_takeover"},
            "department": "Trust & Safety (Fraud & Security)",
            "supporting_departments": ["Compliance & Legal Affairs"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1008",
            "escalation_required": True,
            "escalation_level": "Tier 3 Fraud Security Desk",
            "required_actions": ["Lock account credentials immediately", "Verify buyer identity", "Notify Fraud Response Lead"],
            "prohibited_actions": ["Do not unlock account without government photo ID verification"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@velvocart.com",
            "created_at": "2026-02-02T09:00:00Z",
            "updated_at": "2026-02-02T09:00:00Z"
        },
        {
            "rule_id": "RULE-0123",
            "category": "Regulatory & Legal Compliance",
            "subcategory": "Formal Legal Notice / Attorney Involvement",
            "conditions": {"legal_regulatory_threat": True},
            "department": "Compliance & Legal Affairs",
            "supporting_departments": ["Executive Escalations & Customer Relations"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1009",
            "escalation_required": True,
            "escalation_level": "Chief Legal Officer Review",
            "required_actions": ["Route directly to Legal Compliance desk", "Preserve order, chat, and transaction logs"],
            "prohibited_actions": ["Do not attempt informal settlement without Legal sign-off"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@velvocart.com",
            "created_at": "2026-02-02T09:30:00Z",
            "updated_at": "2026-02-02T09:30:00Z"
        },
        {
            "rule_id": "RULE-0124",
            "category": "Marketplace & Seller Operations",
            "subcategory": "Fraudulent Seller Listing",
            "conditions": {"seller_violation_type": "fake_listing"},
            "department": "Marketplace & Seller Operations",
            "supporting_departments": ["Trust & Safety (Fraud & Security)"],
            "urgency": "Critical",
            "priority": "Urgent",
            "policy_id": "KB-DOC-1007",
            "escalation_required": True,
            "escalation_level": "Marketplace Risk Desk",
            "required_actions": ["Suspend seller store account", "Hold seller balance payout", "Initiate buyer refund process"],
            "prohibited_actions": ["Do not release escrow funds to seller while fraud investigation is active"],
            "follow_up_required": True,
            "is_active": True,
            "created_by": "admin@velvocart.com",
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

    print(f"Generated {total_count} total rules for VelvoCart.")
    print(f"Escalation required rules: {escalation_count}")

    # Export to config/rule_matrix_seed.json
    with open(SEED_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "config_version": "2.0",
            "last_updated": "2026-09-26",
            "total_rules": total_count,
            "escalation_required_count": escalation_count,
            "rules": rules
        }, f, indent=2)

    print(f"Exported seed data to {SEED_OUTPUT_FILE}")

    # Seed database/in-memory store
    try:
        from backend.src.store import RULE_MATRIX_STORE
        RULE_MATRIX_STORE.clear()
        RULE_MATRIX_STORE.extend(rules)
        print(f"Populated in-memory RULE_MATRIX_STORE with {len(RULE_MATRIX_STORE)} rules.")
    except Exception as e:
        print(f"Store seed note: {e}")

    try:
        from backend.database.db import init_db, SessionLocal, HAS_SQLALCHEMY
        from backend.database.models import RuleMatrixModel, KnowledgeDocumentModel
        if HAS_SQLALCHEMY and SessionLocal:
            init_db()
            db = SessionLocal()
            try:
                # Clear old rules
                db.query(RuleMatrixModel).delete()
                db.commit()

                # Add new rules
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
                        created_by=r.get("created_by", "admin@velvocart.com"),
                    )
                    db.add(db_rule)
                db.commit()
                print(f"Populated database table 'rule_matrix' with {len(rules)} new entries.")
            except Exception as e:
                db.rollback()
                print(f"Database seed note: {e}")
            finally:
                db.close()
    except Exception as err:
        print(f"Database seed skipped: {err}")


if __name__ == "__main__":
    main()
