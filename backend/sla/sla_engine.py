from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.models import SLARecord, Complaint

SLA_MATRIX = {
    "P0 – Critical": {"response_hours": 2, "resolution_hours": 12},
    "P1 – High": {"response_hours": 4, "resolution_hours": 24},
    "P2 – Medium": {"response_hours": 8, "resolution_hours": 48},
    "P3 – Low": {"response_hours": 24, "resolution_hours": 72}
}

def create_or_update_sla(db: Session, complaint: Complaint, priority: str) -> SLARecord:
    sla_config = SLA_MATRIX.get(priority, SLA_MATRIX["P3 – Low"])
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    resp_deadline = now + timedelta(hours=sla_config["response_hours"])
    res_deadline = now + timedelta(hours=sla_config["resolution_hours"])
    
    sla_rec = db.query(SLARecord).filter(SLARecord.complaint_id == complaint.id).first()
    if not sla_rec:
        sla_rec = SLARecord(
            complaint_id=complaint.id,
            response_deadline=resp_deadline,
            resolution_deadline=res_deadline,
            status="ON_TRACK"
        )
        db.add(sla_rec)
    else:
        sla_rec.response_deadline = resp_deadline
        sla_rec.resolution_deadline = res_deadline
        
    db.commit()
    db.refresh(sla_rec)
    return sla_rec

def evaluate_sla_status(sla_rec: SLARecord) -> str:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if sla_rec.resolution_met_at:
        return "RESOLVED_ON_TIME"
        
    if now > sla_rec.resolution_deadline:
        return "BREACHED"
        
    time_remaining = sla_rec.resolution_deadline - now
    if time_remaining < timedelta(hours=4):
        return "AT_RISK"
        
    return "ON_TRACK"
