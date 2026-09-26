import io
import json
import csv
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Complaint, GenAIAnalysis, PythonValidation, Comparison, AuditLog

def generate_csv_complaints_report(db: Session) -> str:
    complaints = db.query(Complaint).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Complaint ID", "Title", "Customer Type", "Product/Service", "Channel",
        "Submitted At", "Status", "Priority", "Urgency", "Sentiment",
        "GenAI Category", "Python Category", "GenAI Department", "Python Department",
        "Comparison Status", "Overall Score", "Is Duplicate", "Prompt Injection Flag"
    ])
    
    for c in complaints:
        genai_cat = c.genai_analysis.category if c.genai_analysis else "N/A"
        py_cat = c.python_validation.verified_category if c.python_validation else "N/A"
        genai_dept = c.genai_analysis.department if c.genai_analysis else "N/A"
        py_dept = c.python_validation.verified_department if c.python_validation else "N/A"
        comp_status = c.comparison.overall_status if c.comparison else "N/A"
        score = c.comparison.overall_verification_score if c.comparison else 0.0
        
        writer.writerow([
            c.complaint_code, c.title, c.customer_type, c.product_service or "", c.channel,
            c.submitted_at.isoformat() if c.submitted_at else "", c.status, c.priority, c.urgency, c.sentiment,
            genai_cat, py_cat, genai_dept, py_dept,
            comp_status, score, c.is_duplicate, c.prompt_injection_flag
        ])
        
    return output.getvalue()

def generate_100_case_comparison_report(db: Session) -> Dict[str, Any]:
    """
    Generates 100-Case Evaluation Comparison Report as specified in SRS requirement #57.
    """
    complaints = db.query(Complaint).all()
    evaluation_list = []
    
    matches = 0
    mismatches = 0
    warnings = 0
    reviews = 0
    total_score_sum = 0.0
    
    for c in complaints:
        if not c.genai_analysis or not c.python_validation or not c.comparison:
            continue
            
        genai = c.genai_analysis
        py = c.python_validation
        comp = c.comparison
        
        if comp.overall_status == "MATCH":
            matches += 1
        elif comp.overall_status == "MISMATCH":
            mismatches += 1
        elif comp.overall_status == "WARNING":
            warnings += 1
        elif comp.overall_status == "REVIEW REQUIRED":
            reviews += 1
            
        total_score_sum += comp.overall_verification_score
        
        disagreement_reasons = [m.get("reason") for m in (comp.mismatches or [])]
        
        evaluation_list.append({
            "complaint_id": c.complaint_code,
            "title": c.title,
            "expected_category": py.verified_category,
            "genai_category": genai.category,
            "python_category": py.verified_category,
            "expected_department": py.verified_department,
            "genai_department": genai.department,
            "python_department": py.verified_department,
            "genai_urgency": genai.urgency,
            "python_urgency": py.verified_urgency,
            "genai_escalation": genai.escalation_required,
            "python_escalation": py.verified_escalation_required,
            "policy_references": [p.get("doc_id") for p in (genai.policy_references or [])],
            "comparison_status": comp.overall_status,
            "verification_score": comp.overall_verification_score,
            "reasons_for_disagreement": disagreement_reasons
        })
        
    total_evaluated = len(evaluation_list)
    avg_score = round(total_score_sum / total_evaluated, 2) if total_evaluated > 0 else 100.0
    
    return {
        "summary": {
            "total_cases_evaluated": total_evaluated,
            "total_matches": matches,
            "total_mismatches": mismatches,
            "total_warnings": warnings,
            "total_reviews_required": reviews,
            "average_verification_score": avg_score,
            "agreement_rate_percentage": round((matches / total_evaluated) * 100, 2) if total_evaluated > 0 else 100.0
        },
        "cases": evaluation_list
    }
