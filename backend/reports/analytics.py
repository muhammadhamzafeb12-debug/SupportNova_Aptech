"""
SupportNova Analytics & Trend Detection Engine
backend/reports/analytics.py
"""
import io
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.src.store import (
    COMPLAINTS_STORE,
    RULE_MATRIX_STORE,
    KNOWLEDGE_BASE_STORE,
    AUDIT_LOGS_STORE
)
from backend.complaint_processing.sla import compute_sla_status


def compute_admin_kpis() -> Dict[str, Any]:
    """
    Computes real-time admin KPIs for SupportNova platform.
    """
    all_complaints = list(COMPLAINTS_STORE)
    total_complaints = len(all_complaints)
    
    resolved_statuses = {"resolved", "closed"}
    resolved_count = len([c for c in all_complaints if str(c.get("status", "")).lower() in resolved_statuses])
    open_count = total_complaints - resolved_count
    
    escalations_count = len([
        c for c in all_complaints 
        if str(c.get("status", "")).lower() == "escalated" 
        or c.get("escalation_required") is True
    ])

    # SLA at risk calculation
    sla_at_risk_count = 0
    for c in all_complaints:
        if str(c.get("status", "")).lower() not in resolved_statuses:
            sla_info = compute_sla_status(c)
            is_at_risk = getattr(sla_info, "is_at_risk", False) if hasattr(sla_info, "is_at_risk") else (sla_info.get("is_at_risk") if isinstance(sla_info, dict) else False)
            is_breached = getattr(sla_info, "is_breached", False) if hasattr(sla_info, "is_breached") else (sla_info.get("is_breached") if isinstance(sla_info, dict) else False)
            if is_at_risk or is_breached:
                sla_at_risk_count += 1

    # GenAI / Python Mismatch Rate & Manual Review Queue Size
    from backend.src.api.reviewer import REVIEWER_DECISION_AUDIT
    manual_review_items = [
        c for c in all_complaints 
        if c.get("python_verification_report", {}).get("final_status") == "Manual Review Required"
        or c.get("has_hallucination") is True
        or c.get("python_validation_passed") is False
    ]
    manual_review_queue_size = len(manual_review_items)
    mismatch_rate = round((manual_review_queue_size / total_complaints * 100.0), 1) if total_complaints > 0 else 0.0

    return {
        "total_complaints": total_complaints,
        "open_complaints": open_count,
        "resolved_complaints": resolved_count,
        "escalations_count": escalations_count,
        "sla_at_risk_count": sla_at_risk_count,
        "mismatch_rate": mismatch_rate,
        "manual_review_queue_size": manual_review_queue_size
    }


def calculate_category_trends(now_dt: datetime = None) -> List[Dict[str, Any]]:
    """
    Compares complaint counts over the last 7 days vs previous 7 days per category.
    Flags category as 'rising' if increase > 20%.
    """
    if now_dt is None:
        now_dt = datetime.utcnow()

    seven_days_ago = now_dt - timedelta(days=7)
    fourteen_days_ago = now_dt - timedelta(days=14)

    all_complaints = list(COMPLAINTS_STORE)
    category_counts_recent: Dict[str, int] = {}
    category_counts_prev: Dict[str, int] = {}

    for c in all_complaints:
        cat = c.get("category", "Uncategorized")
        created_str = c.get("created_at")
        
        c_dt = now_dt
        if created_str:
            try:
                c_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                pass

        if c_dt >= seven_days_ago:
            category_counts_recent[cat] = category_counts_recent.get(cat, 0) + 1
        elif c_dt >= fourteen_days_ago:
            category_counts_prev[cat] = category_counts_prev.get(cat, 0) + 1

    # Ensure all present categories are analyzed
    all_categories = set(category_counts_recent.keys()).union(set(category_counts_prev.keys()))
    if not all_categories:
        all_categories = {
            "Billing & Overcharging", 
            "Network Outages & Fiber Disconnection",
            "Hardware & Equipment Faults",
            "SIM & Mobile Network Issues"
        }

    trends = []
    for cat in sorted(all_categories):
        recent = category_counts_recent.get(cat, 0)
        prev = category_counts_prev.get(cat, 0)

        if prev == 0:
            change_pct = float(recent * 100) if recent > 0 else 0.0
        else:
            change_pct = round(((recent - prev) / float(prev)) * 100.0, 1)

        is_rising = change_pct > 20.0
        trend_label = "rising" if is_rising else ("stable" if change_pct >= -20.0 else "declining")

        trends.append({
            "category": cat,
            "recent_count": recent,
            "previous_count": prev,
            "percentage_change": change_pct,
            "is_rising": is_rising,
            "trend_label": trend_label
        })

    return trends


def generate_report_csv(report_type: str) -> str:
    """
    Generates a CSV formatted string for the given report_type.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    all_complaints = list(COMPLAINTS_STORE)

    if report_type == "complaint_analysis":
        writer.writerow(["Complaint ID", "Customer Email", "Category", "Subcategory", "Priority", "Status", "Department", "Sentiment", "Approved Credit", "Created At"])
        for c in all_complaints:
            writer.writerow([
                c.get("complaint_number"),
                c.get("customer_email"),
                c.get("category"),
                c.get("sub_category", ""),
                c.get("priority"),
                c.get("status"),
                c.get("assigned_department"),
                c.get("sentiment_score", 0.5),
                c.get("approved_credit", 0.0),
                c.get("created_at")
            ])

    elif report_type == "department_performance":
        writer.writerow(["Department", "Total Complaints", "Resolved Complaints", "Escalated Complaints", "Total Credits Approved"])
        dept_data: Dict[str, Dict[str, Any]] = {}
        for c in all_complaints:
            d = c.get("assigned_department", "Unassigned")
            if d not in dept_data:
                dept_data[d] = {"total": 0, "resolved": 0, "escalated": 0, "credits": 0.0}
            dept_data[d]["total"] += 1
            if str(c.get("status")).lower() in ["resolved", "closed"]:
                dept_data[d]["resolved"] += 1
            if str(c.get("status")).lower() == "escalated":
                dept_data[d]["escalated"] += 1
            dept_data[d]["credits"] += c.get("approved_credit", 0.0)

        for d, data in dept_data.items():
            writer.writerow([d, data["total"], data["resolved"], data["escalated"], round(data["credits"], 2)])

    elif report_type == "escalations":
        writer.writerow(["Complaint ID", "Customer Email", "Category", "Priority", "Department", "Status", "Escalated At"])
        for c in all_complaints:
            if str(c.get("status")).lower() == "escalated" or c.get("escalation_required"):
                writer.writerow([
                    c.get("complaint_number"),
                    c.get("customer_email"),
                    c.get("category"),
                    c.get("priority"),
                    c.get("assigned_department"),
                    c.get("status"),
                    c.get("updated_at")
                ])

    elif report_type == "sla_status":
        writer.writerow(["Complaint ID", "Category", "Priority", "Status", "Deadline", "Is At Risk", "Is Breached"])
        for c in all_complaints:
            sla_info = compute_sla_status(c)
            deadline = getattr(sla_info, "resolution_deadline", "") if hasattr(sla_info, "resolution_deadline") else (sla_info.get("resolution_deadline") if isinstance(sla_info, dict) else "")
            at_risk = getattr(sla_info, "is_at_risk", False) if hasattr(sla_info, "is_at_risk") else (sla_info.get("is_at_risk") if isinstance(sla_info, dict) else False)
            breached = getattr(sla_info, "is_breached", False) if hasattr(sla_info, "is_breached") else (sla_info.get("is_breached") if isinstance(sla_info, dict) else False)
            writer.writerow([
                c.get("complaint_number"),
                c.get("category"),
                c.get("priority"),
                c.get("status"),
                deadline,
                at_risk,
                breached
            ])

    elif report_type == "policy_usage":
        writer.writerow(["Rule ID", "Category", "Subcategory", "Department", "Priority", "Status", "Min Refund"])
        for r in RULE_MATRIX_STORE:
            writer.writerow([
                r.get("rule_id"),
                r.get("category"),
                r.get("sub_category"),
                r.get("department"),
                r.get("priority"),
                r.get("status"),
                r.get("refund_policy", {}).get("max_amount", 0.0)
            ])

    elif report_type == "genai_comparison":
        writer.writerow(["Complaint ID", "GenAI Category", "Python Category", "GenAI Dept", "Python Dept", "Passed", "Final Status"])
        for c in all_complaints:
            rep = c.get("python_verification_report", {})
            genai_res = c.get("genai_analysis_result", {})
            writer.writerow([
                c.get("complaint_number"),
                genai_res.get("category", c.get("category")),
                c.get("category"),
                genai_res.get("assigned_department", c.get("assigned_department")),
                c.get("assigned_department"),
                c.get("python_validation_passed", True),
                rep.get("final_status", "Auto Approved")
            ])

    elif report_type == "manual_reviews":
        writer.writerow(["Review ID", "Complaint ID", "Action Taken", "Reviewer", "Timestamp", "Override Status"])
        from backend.src.api.reviewer import REVIEWER_DECISION_AUDIT
        for rev in REVIEWER_DECISION_AUDIT:
            writer.writerow([
                rev.get("id"),
                rev.get("complaint_number"),
                rev.get("action"),
                rev.get("reviewer"),
                rev.get("timestamp"),
                rev.get("action") in ["modify", "reclassify", "reassign", "override"]
            ])
    else:
        writer.writerow(["Key", "Value"])
        writer.writerow(["Total Complaints", len(all_complaints)])
        writer.writerow(["Export Date", datetime.utcnow().isoformat()])

    return output.getvalue()


def generate_report_pdf(report_type: str = "summary") -> bytes:
    """
    Generates a PDF binary report for Complaint Intelligence summary.
    """
    # Simple valid PDF binary generator
    kpis = compute_admin_kpis()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    text_lines = [
        "SupportNova Enterprise Complaint Intelligence Report",
        f"Generated On: {now_str}",
        "--------------------------------------------------",
        f"Total Complaints: {kpis['total_complaints']}",
        f"Open Complaints: {kpis['open_complaints']}",
        f"Resolved Complaints: {kpis['resolved_complaints']}",
        f"Escalations Count: {kpis['escalations_count']}",
        f"SLA At-Risk Count: {kpis['sla_at_risk_count']}",
        f"GenAI/Python Mismatch Rate: {kpis['mismatch_rate']}%",
        f"Manual Review Queue Size: {kpis['manual_review_queue_size']}",
        "--------------------------------------------------",
        "NexaLink Communications -- Confidential Operational Intelligence"
    ]

    # Minimal valid PDF structure
    content = "\n".join(text_lines)
    pdf_bytes = (
        f"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        f"4 0 obj\n<< /Length {len(content) + 50} >>\nstream\nBT /F1 12 Tf 50 700 Td ({content}) Tj ET\nendstream\nendobj\n"
        f"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        f"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000244 00000 n \n0000000350 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n430\n%%EOF"
    ).encode("utf-8")
    
    return pdf_bytes
