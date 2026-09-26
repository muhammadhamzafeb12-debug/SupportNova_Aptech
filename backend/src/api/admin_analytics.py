"""
Admin Analytics & Reports Export API Router
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import StreamingResponse
from backend.security.jwt_auth import require_role, get_current_user
from backend.reports.analytics import (
    compute_admin_kpis,
    calculate_category_trends,
    generate_report_csv,
    generate_report_pdf
)

router = APIRouter(prefix="/admin", tags=["Admin Analytics & Reports"])

@router.get("/analytics/kpis")
def get_admin_kpis(
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
) -> Dict[str, Any]:
    return compute_admin_kpis()


@router.get("/analytics/trends")
def get_category_trends(
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager", "Reviewer"))
) -> List[Dict[str, Any]]:
    return calculate_category_trends()


@router.get("/reports/export/{report_type}")
def export_report(
    report_type: str,
    format: Optional[str] = Query("csv"),
    current_user: dict = Depends(require_role("Admin", "Administrator", "Manager"))
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
