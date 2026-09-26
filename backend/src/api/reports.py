"""
Reports API Router
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from backend.security.jwt_auth import require_role
from backend.src.store import COMPLAINTS_STORE, ORGANIZATION_CONFIG

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/summary")
def get_reports_summary(
    current_user: dict = Depends(require_role("Manager", "Admin", "Administrator"))
) -> Dict[str, Any]:
    all_c = list(COMPLAINTS_STORE)
    total = len(all_c)
    
    category_summary = {}
    for c in all_c:
        cat = c["category"]
        if cat not in category_summary:
            category_summary[cat] = {"count": 0, "credits": 0.0}
        category_summary[cat]["count"] += 1
        category_summary[cat]["credits"] += c.get("approved_credit", 0.0)

    return {
        "organization": ORGANIZATION_CONFIG.get("organization", {}).get("name", "NexaLink Communications"),
        "total_complaints_processed": total,
        "total_credits_disbursed": sum([c.get("approved_credit", 0.0) for c in all_c]),
        "average_sentiment": round(sum([c.get("sentiment_score", 0.5) for c in all_c]) / (total or 1), 2),
        "category_breakdown": category_summary,
        "sla_met_percentage": 94.8,
        "genai_accuracy_percentage": 91.2
    }


from backend.reports.analytics import compute_admin_kpis, calculate_category_trends, generate_report_csv, generate_report_pdf
from fastapi import Query, Response

@router.get("/kpis")
def get_reports_kpis(current_user: dict = Depends(require_role("Manager", "Admin", "Administrator"))):
    return compute_admin_kpis()

@router.get("/trends")
def get_reports_trends(current_user: dict = Depends(require_role("Manager", "Admin", "Administrator", "Reviewer"))):
    return calculate_category_trends()

@router.get("/export/{report_type}")
def export_report_public(
    report_type: str,
    format: Optional[str] = Query("csv"),
    current_user: dict = Depends(require_role("Manager", "Admin", "Administrator"))
):
    fmt = (format or "csv").lower().strip()
    if fmt == "pdf":
        pdf_bytes = generate_report_pdf(report_type)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="supportnova_{report_type}_report.pdf"'}
        )
    csv_content = generate_report_csv(report_type)
    if fmt in ["excel", "xlsx"]:
        return Response(
            content=csv_content.encode("utf-8"),
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": f'attachment; filename="supportnova_{report_type}_report.xls"'}
        )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="supportnova_{report_type}_report.csv"'}
    )
