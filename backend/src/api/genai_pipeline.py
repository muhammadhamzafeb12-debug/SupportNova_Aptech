"""
GenAI Pipeline API Router
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.schemas import PipelineTriggerRequest
from backend.security.jwt_auth import require_role
from backend.src.store import COMPLAINTS_STORE

router = APIRouter(prefix="/genai_pipeline", tags=["GenAI Pipeline"])

@router.post("/process")
def process_genai_pipeline(
    payload: PipelineTriggerRequest,
    current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))
) -> Dict[str, Any]:
    target = None
    for c in COMPLAINTS_STORE:
        if c["id"] == payload.complaint_id or str(c["id"]) == str(payload.complaint_id):
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # GenAI Processing Logic simulation
    desc = target["description"]
    sentiment = max(0.05, min(0.95, round(1.0 - (len(desc) / 400.0), 2)))
    
    target["sentiment_score"] = sentiment
    target["genai_summary"] = f"AI Summary: Core dispute regarding {target['category']}. Customer expresses dissatisfaction."
    target["genai_suggested_response"] = (
        f"Dear {target['customer_name']},\n\n"
        f"Thank you for reaching out to NexaLink Communications. We have reviewed your case regarding '{target['title']}'. "
        f"We are committed to providing seamless service and have forwarded this to our {target['assigned_department']} team for resolution.\n\n"
        f"Sincerely,\nSupportNova Care Team"
    )
    target["genai_confidence"] = 0.91

    return {
        "complaint_id": target["id"],
        "status": "Completed",
        "sentiment_score": sentiment,
        "summary": target["genai_summary"],
        "suggested_response": target["genai_suggested_response"],
        "confidence": target["genai_confidence"]
    }

@router.get("/status/{complaint_id}")
def get_pipeline_status(
    complaint_id: int,
    current_user: dict = Depends(require_role("Agent", "Reviewer", "Manager", "Admin", "Administrator"))
):
    for c in COMPLAINTS_STORE:
        if c["id"] == complaint_id:
            return {
                "complaint_id": complaint_id,
                "pipeline_state": "Ready",
                "genai_confidence": c.get("genai_confidence", 0.85),
                "processed": c.get("genai_summary") is not None
            }
    raise HTTPException(status_code=404, detail="Complaint not found")
