"""
SLA & Follow-Up API — SupportNova
===================================
Endpoints:
  GET  /admin/sla-targets              — read current SLA targets
  PUT  /admin/sla-targets              — admin update (live config, on-disk)
  GET  /sla/risk                       — open complaints that are at-risk or breached
  GET  /sla/{id}/follow-ups
  POST /sla/{id}/follow-ups
  POST /sla/{id}/follow-ups/{fuid}/complete

NOTE: SLA routes use /sla/* prefix (not /complaints/*) to avoid collision
with the existing /complaints/{identifier} wildcard route in complaints.py.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.security.jwt_auth import get_current_user, require_role
from backend.complaint_processing.sla import (
    compute_sla_status,
    get_sla_targets,
    update_sla_targets,
    FOLLOW_UP_TYPES,
)
from backend.src.store import COMPLAINTS_STORE
from backend.src.api.reviewer import FOLLOW_UPS_STORE

# ── Routers ──────────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/admin", tags=["Admin SLA"])
sla_router   = APIRouter(prefix="/sla", tags=["SLA & Follow-Ups"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SLATargetUpdate(BaseModel):
    P0: Optional[Dict[str, Any]] = None
    P1: Optional[Dict[str, Any]] = None
    P2: Optional[Dict[str, Any]] = None
    P3: Optional[Dict[str, Any]] = None


class FollowUpCreate(BaseModel):
    due_date: str
    follow_up_type: str


# ── Admin SLA target endpoints ────────────────────────────────────────────────

@admin_router.get("/sla-targets")
def read_sla_targets(
    current_user: Dict[str, Any] = Depends(require_role("Agent","Reviewer","Manager","Admin","Administrator")),
):
    return get_sla_targets()


@admin_router.put("/sla-targets")
def write_sla_targets(
    body: SLATargetUpdate,
    current_user: Dict[str, Any] = Depends(require_role("Admin","Administrator")),
):
    current = get_sla_targets()
    updates = body.model_dump(exclude_none=True)
    for tier, vals in updates.items():
        if tier in current:
            current[tier].update(vals)
        else:
            current[tier] = vals
    saved = update_sla_targets(current)
    return {"success": True, "sla_targets": saved}


# ── SLA Risk endpoint ─────────────────────────────────────────────────────────

OPEN_STATUSES = frozenset({
    "New", "Analyzed", "Assigned", "In Progress",
    "Awaiting Customer", "Escalated", "Reopened",
    # legacy aliases
    "Submitted", "In Review", "Review Required", "Under Review",
})


@sla_router.get("/risk")
def get_sla_risk(
    current_user: Dict[str, Any] = Depends(require_role("Agent","Reviewer","Manager","Admin","Administrator")),
):
    """
    Lists all open complaints that are is_at_risk or is_breached,
    sorted most-urgent-first (breached first, then by time_remaining ascending).
    """
    targets = get_sla_targets()
    results = []
    for c in COMPLAINTS_STORE:
        if c.get("status") not in OPEN_STATUSES:
            continue
        sla = compute_sla_status(c, sla_targets=targets)
        if sla.is_at_risk or sla.is_breached:
            results.append({
                "id": c["id"],
                "complaint_number": c["complaint_number"],
                "title": c.get("title", ""),
                "category": c.get("category", ""),
                "priority": c.get("priority", ""),
                "status": c.get("status", ""),
                "customer_name": c.get("customer_name", ""),
                "assigned_agent": c.get("assigned_agent"),
                "sla": sla.to_dict(),
            })

    # Sort: breached first, then soonest deadline first
    results.sort(key=lambda x: (
        not x["sla"]["is_breached"],
        x["sla"]["time_remaining_hours"],
    ))
    return {"total": len(results), "items": results}


# ── Follow-up endpoints ───────────────────────────────────────────────────────

def _find_complaint(complaint_id: str) -> Dict[str, Any]:
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == complaint_id or c["complaint_number"].lower() == complaint_id.lower():
            return c
    raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")


@sla_router.get("/{complaint_id}/follow-ups")
def list_follow_ups(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    complaint = _find_complaint(complaint_id)
    cid = str(complaint["id"])
    items = [f for f in FOLLOW_UPS_STORE if str(f.get("complaint_id")) == cid]
    return {"complaint_id": cid, "follow_ups": items}


@sla_router.post("/{complaint_id}/follow-ups", status_code=201)
def create_follow_up(
    complaint_id: str,
    body: FollowUpCreate,
    current_user: Dict[str, Any] = Depends(require_role("Agent","Reviewer","Manager","Admin","Administrator")),
):
    if body.follow_up_type not in FOLLOW_UP_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown follow_up_type '{body.follow_up_type}'. "
                   f"Allowed: {sorted(FOLLOW_UP_TYPES)}",
        )
    complaint = _find_complaint(complaint_id)
    cid = str(complaint["id"])
    fu = {
        "id": f"FU-{len(FOLLOW_UPS_STORE)+1:04d}",
        "complaint_id": cid,
        "complaint_number": complaint["complaint_number"],
        "due_date": body.due_date,
        "follow_up_type": body.follow_up_type,
        "completed": False,
        "completed_at": None,
        "created_by": current_user.get("username"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    FOLLOW_UPS_STORE.append(fu)
    return fu


@sla_router.post("/{complaint_id}/follow-ups/{follow_up_id}/complete")
def complete_follow_up(
    complaint_id: str,
    follow_up_id: str,
    current_user: Dict[str, Any] = Depends(require_role("Agent","Reviewer","Manager","Admin","Administrator")),
):
    complaint = _find_complaint(complaint_id)
    cid = str(complaint["id"])
    target = next(
        (f for f in FOLLOW_UPS_STORE if f["id"] == follow_up_id and str(f["complaint_id"]) == cid),
        None,
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Follow-up '{follow_up_id}' not found")
    if target["completed"]:
        raise HTTPException(status_code=400, detail="Follow-up already marked complete")
    target["completed"] = True
    target["completed_at"] = datetime.now(timezone.utc).isoformat()
    return target
