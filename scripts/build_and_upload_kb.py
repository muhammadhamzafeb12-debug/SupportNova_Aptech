"""
Build and upload 21 VelvoCart E-Commerce Knowledge Base Documents.
Replaces all old NexaLink telecom documents.
Populates KNOWLEDGE_BASE_STORE and KB_CHUNKS_STORE using process_document_pipeline.
"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DOCS_DIR = PROJECT_ROOT / "sample_documents"


DOCUMENTS_SPEC = [
    {
        "id": "KB-DOC-1001",
        "title": "VelvoCart Return Policy 2026",
        "category": "policy",
        "version": "2.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Return_Policy_2026.txt",
        "content": """# VelvoCart Return Policy 2026 (Active v2.0)

1. RETURN WINDOW & ELIGIBILITY
VelvoCart customers are entitled to return eligible items within 30 days of delivery date. Items must be in original, unwashed, unworn condition with all original tags attached.

2. RETURN PROCESS
Returns can be requested online via the VelvoCart Returns Portal. Items must be dropped off at any authorized VelvoCart Return Hub location or shipped using a pre-paid printable return label.

3. RESTOCKING & SHIPPING FEES
Standard returns incur no restocking fees. Return shipping is free for VelvoCart Prime members and for orders returned due to merchant error, defective items, or wrong size delivered. Standard non-Prime returns carry a flat $4.99 return shipping fee deducted from the final refund amount.

4. NON-RETURNABLE ITEMS
Perishable groceries, opened hygiene goods, unsealed software, gift cards, and final clearance items are strictly non-returnable unless arrived damaged or defective.
"""
    },
    {
        "id": "KB-DOC-1002",
        "title": "VelvoCart Refund Policy 2026",
        "category": "policy",
        "version": "2.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Refund_Policy_2026.txt",
        "content": """# VelvoCart Refund Policy 2026 (Active v2.0)

1. REFUND TIMELINE
Once a returned item is received and scanned at a VelvoCart Return Hub, refunds are processed within 3 to 5 business days.

2. REFUND METHODS
Refunds will be credited to the original payment method (Credit/Debit card, PayPal, or VelvoPay Wallet). Buyers selecting VelvoPay Wallet Store Credit receive instant refund credit upon carrier drop-off scan.

3. PARTIAL REFUNDS & ADJUSTMENTS
Items returned with missing accessories, damaged box packaging, or signs of usage beyond inspection may receive a partial refund subject to a 15% to 30% restocking fee.
"""
    },
    {
        "id": "KB-DOC-1003",
        "title": "VelvoCart Delivery & Logistics Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Delivery_Logistics_Policy.txt",
        "content": """# VelvoCart Delivery & Logistics Policy

1. SAME-DAY & STANDARD SHIPPING SLA
VelvoCart Prime Same-Day delivery orders placed before 12:00 PM are guaranteed for delivery by 9:00 PM the same calendar day. Standard fulfillment orders ship within 24 to 48 hours with expected delivery in 3 to 5 business days.

2. LOST PACKAGE & TRANSIT CLAIMS
If a package tracking status has not updated for 5 consecutive calendar days or shows delivered but is missing, customers may submit a Lost Package Claim for immediate free reshipment or 100% full refund.
"""
    },
    {
        "id": "KB-DOC-1004",
        "title": "VelvoCart Damaged and Lost Item Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Damaged_Lost_Item_Policy.txt",
        "content": """# VelvoCart Damaged and Lost Item Policy

1. REPORTING DAMAGE
Damaged goods must be reported within 48 hours of delivery receipt. Customers must provide digital photo evidence showing outer shipping container damage and item product defect.

2. IMMEDIATE REPLACEMENT PROTOCOL
Upon confirmation of carrier damage or concealed shipping defect, VelvoCart will dispatch an immediate replacement unit via Same-Day Express Delivery at no additional cost.
"""
    },
    {
        "id": "KB-DOC-1005",
        "title": "VelvoCart Billing and Payment Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Billing_Payment_Policy.txt",
        "content": """# VelvoCart Billing and Payment Policy

1. PAYMENT AUTHORIZATION
All checkouts require valid payment authorization. VelvoCart accepts credit cards, debit cards, VelvoPay Digital Wallet balances, and official VelvoCart Gift Cards.

2. DUPLICATE & INCORRECT CHARGES
In the event of duplicate billing or checkout price mismatch, customers must report the billing anomaly within 30 days of invoice date to receive instant full credit adjustment.
"""
    },
    {
        "id": "KB-DOC-1006",
        "title": "VelvoCart Gift Card & Voucher Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Gift_Card_Policy.txt",
        "content": """# VelvoCart Gift Card Policy

1. REDEMPTION & EXPIRATION
VelvoCart Digital Gift Cards never expire and carry no inactivity fees. Gift card balances can be redeemed storewide for any item including Prime subscriptions.

2. NON-REFUNDABLE TERMS
Gift card purchases are non-refundable and cannot be redeemed for cash unless required by applicable state law.
"""
    },
    {
        "id": "KB-DOC-1007",
        "title": "VelvoCart Marketplace 3rd-Party Seller Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Marketplace_Seller_Policy.txt",
        "content": """# VelvoCart Marketplace 3rd-Party Seller Policy

1. SELLER SLA RESPONSIBILITIES
Independent marketplace sellers must respond to buyer messages and return requests within 48 business hours. Sellers failing to respond within 48 hours are subject to automatic buyer refund override.

2. A-TO-Z BUYER PROTECTION
If a third-party seller delivers a counterfeit, defective, or misdescribed product, VelvoCart's A-to-Z Buyer Guarantee covers 100% of order cost and return shipping.
"""
    },
    {
        "id": "KB-DOC-1008",
        "title": "VelvoCart Fraud and Account Security Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Fraud_Account_Security_Policy.txt",
        "content": """# VelvoCart Fraud & Account Security Policy

1. UNAUTHORIZED PURCHASES
VelvoCart maintains a zero-liability policy for verified unauthorized account activity. Orders flagged for account takeover or stolen credit card fraud are cancelled immediately with 100% fund reversal.

2. ACCOUNT LOCK & IDENTITY VERIFICATION
Accounts exhibiting suspicious login attempts or unauthorized password reset requests are locked by Trust & Safety. Unlocking requires official government photo ID verification.
"""
    },
    {
        "id": "KB-DOC-1009",
        "title": "VelvoCart Data Privacy & Compliance Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Data_Privacy_Policy.txt",
        "content": """# VelvoCart Data Privacy Policy

1. CCPA & GDPR COMPLIANCE
VelvoCart adheres to strict international data privacy standards under CCPA and GDPR. Customers possess the absolute right to request data access, portability, or complete account deletion.

2. PRIVACY COMPLAINT ESCALATION
All privacy infringement allegations, data leak notices, or attorney communications must be routed immediately to Compliance & Legal Affairs (DEPT-008) for priority handling within 2 hours.
"""
    },
    {
        "id": "KB-DOC-1010",
        "title": "VelvoCart Customer Protection Plan Terms",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Customer_Protection_Plan_Terms.txt",
        "content": """# VelvoCart Customer Protection Plan Terms

1. EXTENDED WARRANTY COVERAGE
The VelvoCart Customer Protection Plan extends manufacturer warranty coverage for 2 additional years. Covers mechanical breakdowns, electrical surge damage, and battery degradation.

2. SAFETY HAZARD RECALL & REPLACEMENT
If a product is flagged for safety hazard, overheating, or battery fire risk, protection plan holders receive immediate free replacement with no deductible.
"""
    },
    {
        "id": "KB-DOC-1011",
        "title": "VelvoCart Escalation Procedure SOP",
        "category": "sop",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Escalation_Procedure_SOP.txt",
        "content": """# VelvoCart Escalation Procedure SOP

1. PURPOSE
Defines operational escalation paths for high-priority customer complaints exceeding standard SLA bounds.

2. ESCALATION TRIGGERS
- Repeat complaints (3+ unresolved attempts on same order ID)
- Safety hazard or counterfeit product report
- Attorney letter or regulatory regulator filing (FTC/BBB)
- Financial dispute exceeding $500

3. ROUTING PROTOCOL
Tier 1 agents must escalate eligible cases to Tier 2 Operations Managers or Executive Escalations (DEPT-009) within 15 minutes of identification.
"""
    },
    {
        "id": "KB-DOC-1012",
        "title": "VelvoCart Customer Complaint Handling SOP",
        "category": "sop",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Complaint_Handling_SOP.txt",
        "content": """# VelvoCart Complaint Handling SOP

1. COMPLAINT INTAKE & LOGGING
Every customer interaction must record: Order ID, Buyer Email, Primary Category, Priority Level, and Resolution Action Taken.

2. EMPOWERMENT LIMITS
Customer Service Agents are authorized to issue bill credits or refunds up to $50 without supervisor approval. Requests between $51 and $200 require Tier 2 Manager sign-off.
"""
    },
    {
        "id": "KB-DOC-1013",
        "title": "VelvoCart Department Routing Rules SOP",
        "category": "sop",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Department_Routing_Rules.txt",
        "content": """# VelvoCart Department Routing Rules SOP

SECTION 1: FULFILLMENT ROUTING
Order & delivery disputes must be auto-routed to DEPT-001 (Fulfillment & Logistics).

SECTION 2: PAYMENTS ROUTING
Billing, refund, and payment gateway disputes must be auto-routed to DEPT-002 (Billing & Payments).

SECTION 3: RETURNS ROUTING
Return requests and return shipping disputes must be auto-routed to DEPT-003 (Returns & Reverse Logistics).

SECTION 4: QUALITY ROUTING
Product defect, authenticity, and counterfeit reports must be auto-routed to DEPT-004 (Product Quality).

SECTION 5: SECURITY ROUTING
Account takeover, credit card fraud, and phishing reports must be auto-routed to DEPT-006 (Trust & Safety).

SECTION 6: MARKETPLACE ROUTING
Third-party marketplace seller disputes must be auto-routed to DEPT-007 (Marketplace Operations).

SECTION 7: LEGAL ROUTING
Data privacy law complaints, attorney letters, and regulatory filings must be auto-routed to DEPT-008 (Compliance & Legal Affairs).
"""
    },
    {
        "id": "KB-DOC-1014",
        "title": "VelvoCart SLA Service Level Agreement Policy",
        "category": "policy",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_SLA_Service_Level_Agreement.txt",
        "content": """# VelvoCart SLA Policy

1. SLA TARGET RESOLUTION TIMES
- P0 Critical (Security/Fraud/Safety): Response 1 hour, Resolution 12 hours.
- P1 High (Order Lost/Damaged Electronics): Response 4 hours, Resolution 24 hours.
- P2 Medium (Standard Returns/Billing): Response 8 hours, Resolution 48 hours.
- P3 Low (General Inquiry/Promo Code): Response 24 hours, Resolution 72 hours.
"""
    },
    {
        "id": "KB-DOC-1015",
        "title": "VelvoCart Outdated Return SOP 2024 (CONTRADICTORY)",
        "category": "sop",
        "version": "1.0",
        "status": "Deprecated",
        "effective_date": "2024-01-01",
        "filename": "VelvoCart_Outdated_Return_SOP_2024.txt",
        "content": """# VelvoCart Outdated Return SOP 2024 (DEPRECATED v1.0)

NOTE: THIS DOCUMENT IS OUTDATED AND DEPRECATED.

1. DEPRECATED RETURN WINDOW
[OUTDATED v1.0 RULE]: Customers may only return items within 14 calendar days of purchase date. Any return attempt past 14 days must be automatically rejected.

(Contradicted by Active v2.0 Policy KB-DOC-1001 which grants a 30-day return window from delivery date).
"""
    },
    {
        "id": "KB-DOC-1016",
        "title": "VelvoCart Promotional Looser Returns FAQ (CONTRADICTORY)",
        "category": "faq",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Looser_Returns_FAQ.txt",
        "content": """# VelvoCart Marketing FAQ (Looser Return Claims)

Q: What is VelvoCart's holiday return window?
A: During promotional events, VelvoCart offers a loose 60-day hassle-free return window on all orders!

(NOTE: Contradicts official Active Policy KB-DOC-1001 30-day window; ground truth policy KB-DOC-1001 takes legal precedence over promotional marketing FAQ).
"""
    },
    {
        "id": "KB-DOC-1017",
        "title": "VelvoCart Outdated Billing SOP 2024 (CONTRADICTORY)",
        "category": "sop",
        "version": "1.0",
        "status": "Deprecated",
        "effective_date": "2024-01-01",
        "filename": "VelvoCart_Outdated_Billing_SOP_2024.txt",
        "content": """# VelvoCart Outdated Billing SOP 2024 (DEPRECATED v1.0)

NOTE: THIS DOCUMENT IS OUTDATED AND DEPRECATED.

1. DEPRECATED BILLING DISPUTE WINDOW
[OUTDATED v1.0 RULE]: Billing price mismatches must be reported within 60 days of purchase.

(Contradicted by Active Policy KB-DOC-1005 30-day invoice dispute window).
"""
    },
    {
        "id": "KB-DOC-1018",
        "title": "VelvoCart Delivery FAQ",
        "category": "faq",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Delivery_FAQ.txt",
        "content": """# VelvoCart Delivery FAQ

Q: How do I track my delivery?
A: Log into your VelvoCart account, open Order History, and click Track Package. Real-time GPS tracking is available for Same-Day Express orders.
"""
    },
    {
        "id": "KB-DOC-1019",
        "title": "VelvoCart Billing FAQ",
        "category": "faq",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Billing_FAQ.txt",
        "content": """# VelvoCart Billing FAQ

Q: When will my card be charged?
A: Credit cards are authorized at checkout and charged when items enter warehouse dispatch.
"""
    },
    {
        "id": "KB-DOC-1020",
        "title": "VelvoCart Returns FAQ",
        "category": "faq",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Returns_FAQ.txt",
        "content": """# VelvoCart Returns FAQ

Q: Where do I drop off my return package?
A: Drop off return packages at any VelvoCart Return Hub or authorized retail drop-off location.
"""
    },
    {
        "id": "KB-DOC-1021",
        "title": "VelvoCart Marketplace FAQ",
        "category": "faq",
        "version": "1.0",
        "status": "Active",
        "effective_date": "2026-01-01",
        "filename": "VelvoCart_Marketplace_FAQ.txt",
        "content": """# VelvoCart Marketplace FAQ

Q: What if a 3rd-party seller does not respond?
A: If a marketplace seller does not reply within 48 hours, submit an A-to-Z Guarantee claim for an automatic full refund.
"""
    }
]


def main():
    # 1. Clean existing sample_documents directory
    if SAMPLE_DOCS_DIR.exists():
        for item in SAMPLE_DOCS_DIR.iterdir():
            if item.is_file():
                item.unlink()
    else:
        SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Cleaned {SAMPLE_DOCS_DIR}")

    # 2. Write all 21 VelvoCart documents into sample_documents/
    written_files = []
    for doc in DOCUMENTS_SPEC:
        file_path = SAMPLE_DOCS_DIR / doc["filename"]
        file_path.write_text(doc["content"], encoding="utf-8")
        written_files.append(file_path)

    print(f"Created {len(written_files)} VelvoCart e-commerce policy documents.")

    # 3. Process each document through pipeline
    try:
        from backend.src.store import KNOWLEDGE_BASE_STORE, KB_CHUNKS_STORE
        from backend.document_processing.pipeline import process_document_pipeline

        # Clear existing stores
        KNOWLEDGE_BASE_STORE.clear()
        KB_CHUNKS_STORE.clear()

        for doc in DOCUMENTS_SPEC:
            file_path = str(SAMPLE_DOCS_DIR / doc["filename"])
            kb_doc_record = {
                "document_id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "version": doc["version"],
                "status": doc["status"],
                "effective_date": doc["effective_date"],
                "file_name": doc["filename"],
                "file_path": file_path,
                "content_hash": f"hash_velvo_{doc['id']}",
                "parsing_status": "pending",
                "parsing_error": None,
                "chunk_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            KNOWLEDGE_BASE_STORE.append(kb_doc_record)
            process_document_pipeline(
                document_id=doc["id"],
                file_path=file_path,
                version=doc["version"],
                kb_store=KNOWLEDGE_BASE_STORE,
                chunks_store=KB_CHUNKS_STORE
            )

        print(f"Ingested {len(KNOWLEDGE_BASE_STORE)} KB documents into KNOWLEDGE_BASE_STORE!")
        print(f"Total chunks created: {len(KB_CHUNKS_STORE)}")

    except Exception as e:
        print(f"Pipeline ingestion note: {e}")


if __name__ == "__main__":
    main()
