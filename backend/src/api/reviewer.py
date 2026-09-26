"""
Reviewer Workflow API — SupportNova
=====================================
Implements the complete Manual Review Queue and Reviewer Decision system.

Endpoints:
  GET  /reviewer/queue                     — paginated list of Manual Review Required complaints
  POST /reviewer/{complaint_id}/decision   — reviewer action (approve/modify/reclassify/…)
  GET  /reviewer/{complaint_id}/audit-trail — full immutable decision history
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.security.jwt_auth import get_current_user, require_role
from backend.complaint_processing.state_machine import assert_valid_transition
from backend.src.store import (
    COMPLAINTS_STORE,
    VERIFICATION_REPORTS_STORE,
    AUDIT_LOGS_STORE,
)

router = APIRouter(prefix="/reviewer", tags=["Reviewer Workflow"])

# ── In-process stores (module-level, imported by tests) ─────────────────────
# Reviewer decision audit — IMMUTABLE (append-only, never deleted/modified)
REVIEWER_DECISION_AUDIT: List[Dict[str, Any]] = []
# Follow-up records keyed by complaint_id
FOLLOW_UPS_STORE: List[Dict[str, Any]] = []

# ── Schemas ──────────────────────────────────────────────────────────────────

ALLOWED_ACTIONS = frozenset({
    "approve",
    "reject",
    "modify",
    "reclassify",
    "reassign",
    "escalate",
    "regenerate_response",
    "add_comment",
})


class ReviewerDecisionRequest(BaseModel):
    action: str
    payload: Optional[Dict[str, Any]] = {}
    comment: Optional[str] = ""


class FollowUpCreate(BaseModel):
    due_date: str
    follow_up_type: str  # info_request | resolution_confirmation | refund_status | …


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_complaint(complaint_id: str) -> Dict[str, Any]:
    for c in COMPLAINTS_STORE:
        if str(c["id"]) == complaint_id or c["complaint_number"].lower() == complaint_id.lower():
            return c
    raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found")


def _find_report(complaint_id: str) -> Optional[Dict[str, Any]]:
    """Return the most recent VerificationReport for a complaint (or None)."""
    cid_str = str(complaint_id)
    match = None
    for r in VERIFICATION_REPORTS_STORE:
        c_id = str(r.get("complaint_id", ""))
        if c_id == cid_str:
            match = r
    return match


def _write_audit(
    complaint_id: str,
    complaint_number: str,
    reviewer: Dict[str, Any],
    action: str,
    original_genai_value: Any,
    original_python_value: Any,
    reviewer_final_value: Any,
    comment: str,
) -> Dict[str, Any]:
    """Append an immutable audit entry. Always returns the new entry."""
    entry = {
        "id": len(REVIEWER_DECISION_AUDIT) + 1,
        "complaint_id": complaint_id,
        "complaint_number": complaint_number,
        "reviewer_id": reviewer.get("username", "unknown"),
        "reviewer_name": reviewer.get("full_name", ""),
        "action": action,
        "original_genai_value": original_genai_value,
        "original_python_value": original_python_value,
        "reviewer_final_value": reviewer_final_value,
        "comment": comment or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REVIEWER_DECISION_AUDIT.append(entry)

    # Mirror in global audit log
    AUDIT_LOGS_STORE.append({
        "id": len(AUDIT_LOGS_STORE) + 1,
        "complaint_number": complaint_number,
        "action": f"Reviewer Decision: {action}",
        "performed_by": reviewer.get("username", ""),
        "details": comment or f"Reviewer action: {action}",
        "timestamp": entry["timestamp"],
    })
    return entry


def _build_queue_row(complaint: Dict[str, Any], report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    created = complaint.get("created_at", "")
    if created:
        try:
            created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            hours_waiting = round((now - created_dt).total_seconds() / 3600, 1)
        except Exception:
            hours_waiting = 0.0
    else:
        hours_waiting = 0.0

    mismatches = report.get("mismatches", []) if report else []
    # classify mismatch types
    mismatch_types = []
    for m in mismatches:
        ml = m.lower() if isinstance(m, str) else ""
        if "category" in ml:
            mismatch_types.append("category")
        if "department" in ml:
            mismatch_types.append("department")
        if "urgency" in ml:
            mismatch_types.append("urgency")
        if "escalation" in ml:
            mismatch_types.append("escalation")
        if "policy" in ml:
            mismatch_types.append("policy")

    return {
        "id": complaint["id"],
        "complaint_number": complaint["complaint_number"],
        "customer_name": complaint.get("customer_name", ""),
        "customer_email": complaint.get("customer_email", ""),
        "title": complaint.get("title", ""),
        "category": complaint.get("category", ""),
        "sub_category": complaint.get("sub_category", ""),
        "priority": complaint.get("priority", "Medium"),
        "status": complaint.get("status", ""),
        "hours_waiting": hours_waiting,
        "created_at": complaint.get("created_at"),
        "verification_report": report,
        "verification_score": report.get("verification_score") if report else None,
        "mismatch_types": list(set(mismatch_types)),
        "mismatches": mismatches,
    }


# ── GET /reviewer/queue ───────────────────────────────────────────────────────

@router.get("/queue")
def get_review_queue(
    mismatch_type: Optional[str] = Query(None, description="Filter by mismatch type: category|department|urgency|escalation|policy"),
    priority: Optional[str] = Query(None, description="Filter by priority (High, Medium, P0, P1, etc.)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_role("Reviewer", "Manager", "Admin", "Administrator")),
):
    """
    Returns all complaints where VerificationReport.final_status == 'Manual Review Required',
    paginated, with full VerificationReport embedded.
    Sorted oldest-first (highest urgency).
    """
    # Build lookup: complaint_id -> most recent report
    report_map: Dict[str, Dict[str, Any]] = {}
    for r in VERIFICATION_REPORTS_STORE:
        cid = str(r.get("complaint_id", ""))
        if r.get("final_status") == "Manual Review Required":
            report_map[cid] = r

    # Also capture complaints whose status field indicates review needed
    results = []
    seen_ids = set()
    for c in COMPLAINTS_STORE:
        cid = str(c["id"])
        cnum = c.get("complaint_number", "")
        in_report_map = cid in report_map or cnum in report_map

        # Check by complaint_number too
        report = report_map.get(cid) or report_map.get(cnum)

        # A complaint qualifies if it has a Manual Review Required report OR its status says so
        qualifies = (
            report is not None
            or c.get("status") in ("Review Required", "Manual Review Required")
        )

        if not qualifies or cid in seen_ids:
            continue
        seen_ids.add(cid)

        row = _build_queue_row(c, report)

        # Filter by mismatch_type
        if mismatch_type and mismatch_type.lower() not in [m.lower() for m in row["mismatch_types"]]:
            continue

        # Filter by priority
        if priority:
            comp_priority = c.get("priority", "").lower()
            if priority.lower() not in comp_priority:
                continue

        results.append(row)

    # Sort: oldest first
    results.sort(key=lambda x: x.get("hours_waiting", 0), reverse=True)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    items = results[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


# ── POST /reviewer/{complaint_id}/decision ────────────────────────────────────

@router.post("/{complaint_id}/decision")
def reviewer_decision(
    complaint_id: str,
    body: ReviewerDecisionRequest,
    current_user: Dict[str, Any] = Depends(require_role("Reviewer", "Manager", "Admin", "Administrator")),
):
    """
    Record a reviewer decision for a complaint.
    Writes an immutable entry to REVIEWER_DECISION_AUDIT (SRS req lxiii).
    """
    action = body.action.lower().strip()
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{action}'. Allowed: {sorted(ALLOWED_ACTIONS)}",
        )

    complaint = _find_complaint(complaint_id)
    report = _find_report(str(complaint["id"])) or _find_report(complaint.get("complaint_number", ""))

    # Capture original values for audit trail (SRS requirement lxiii)
    genai_result = complaint.get("genai_analysis_result") or {}
    original_genai = {
        "category": genai_result.get("issue_category", complaint.get("category")),
        "department": genai_result.get("department", complaint.get("assigned_department")),
        "urgency": genai_result.get("urgency"),
        "priority": genai_result.get("priority"),
        "escalation_required": genai_result.get("escalation_required"),
        "professional_response": genai_result.get("professional_response"),
    }
    python_report = report or {}
    original_python = {
        "verification_score": python_report.get("verification_score"),
        "final_status": python_report.get("final_status"),
        "mismatches": python_report.get("mismatches", []),
        "overwritten_fields": python_report.get("overwritten_fields", {}),
    }

    reviewer_final: Any = body.payload or {}
    new_status = complaint.get("status", "In Progress")

    # ── Action handlers ───────────────────────────────────────────────────────

    if action == "approve":
        # Accept Python-verified values as final — move complaint forward
        try:
            assert_valid_transition(complaint["status"], "Assigned")
            new_status = "Assigned"
        except ValueError:
            # If transition not legal from current state, try "In Progress"
            try:
                assert_valid_transition(complaint["status"], "In Progress")
                new_status = "In Progress"
            except ValueError:
                new_status = complaint["status"]  # keep as-is
        complaint["status"] = new_status
        reviewer_final = {"accepted_python_values": True, "new_status": new_status}

    elif action == "reject":
        # Reject — keep in review, add comment
        reviewer_final = {"rejected": True, "reason": body.comment}

    elif action == "modify":
        # Reviewer supplies corrected field values — these become authoritative
        payload = body.payload or {}
        if "category" in payload:
            complaint["category"] = payload["category"]
        if "sub_category" in payload:
            complaint["sub_category"] = payload["sub_category"]
        if "priority" in payload:
            complaint["priority"] = payload["priority"]
        if "assigned_department" in payload:
            complaint["assigned_department"] = payload["assigned_department"]
        if "assigned_agent" in payload:
            complaint["assigned_agent"] = payload["assigned_agent"]
        if "resolution_notes" in payload:
            complaint["resolution_notes"] = payload["resolution_notes"]
        if "professional_response" in payload and complaint.get("genai_analysis_result"):
            complaint["genai_analysis_result"]["professional_response"] = payload["professional_response"]
        if "approved_credit" in payload:
            complaint["approved_credit"] = payload["approved_credit"]
        complaint["updated_at"] = datetime.now(timezone.utc).isoformat()
        reviewer_final = payload

    elif action == "reclassify":
        # Change category/subcategory and re-run RuleMatrixEngine
        payload = body.payload or {}
        if "category" in payload:
            complaint["category"] = payload["category"]
        if "sub_category" in payload:
            complaint["sub_category"] = payload["sub_category"]
        # Re-trigger rule engine for fresh context
        try:
            from backend.complaint_rules.engine import RuleMatrixEngine
            engine = RuleMatrixEngine()
            matched = engine.match({
                "category": complaint["category"],
                "subcategory": complaint.get("sub_category", ""),
            })
            if matched:
                complaint["assigned_department"] = matched.department
                if matched.escalation_required:
                    complaint["escalation_required"] = True
                    complaint["escalation_level"] = matched.escalation_level or "Tier 1"
            reviewer_final = {
                "new_category": complaint["category"],
                "matched_rule": matched.rule_id if matched else None,
            }
        except Exception as e:
            reviewer_final = {"new_category": complaint["category"], "rule_engine_error": str(e)}
        complaint["updated_at"] = datetime.now(timezone.utc).isoformat()

    elif action == "reassign":
        payload = body.payload or {}
        if "department" in payload:
            complaint["assigned_department"] = payload["department"]
        if "supporting_departments" in payload:
            complaint["supporting_departments"] = payload["supporting_departments"]
        if "assigned_agent" in payload:
            complaint["assigned_agent"] = payload["assigned_agent"]
        complaint["updated_at"] = datetime.now(timezone.utc).isoformat()
        reviewer_final = payload

    elif action == "escalate":
        payload = body.payload or {}
        complaint["escalation_required"] = True
        complaint["escalation_level"] = payload.get("escalation_level", "Tier 2")
        try:
            assert_valid_transition(complaint["status"], "Escalated")
            complaint["status"] = "Escalated"
            new_status = "Escalated"
        except ValueError:
            pass
        complaint["updated_at"] = datetime.now(timezone.utc).isoformat()
        reviewer_final = {"escalation_level": complaint["escalation_level"], "new_status": new_status}

    elif action == "regenerate_response":
        # Re-trigger Pipeline 1 for professional_response only (async not needed — stub the re-gen)
        # In production this would enqueue a background task; here we mark it pending
        complaint["pipeline1_status"] = "pending_regen"
        complaint["updated_at"] = datetime.now(timezone.utc).isoformat()
        reviewer_final = {"regen_requested": True, "keep_classification": True}

    elif action == "add_comment":
        # Pure comment — no status change
        existing = complaint.get("reviewer_comments", [])
        new_comment = {
            "by": current_user.get("username"),
            "text": body.comment,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        existing.append(new_comment)
        complaint["reviewer_comments"] = existing
        reviewer_final = new_comment

    # Write immutable audit record
    audit_entry = _write_audit(
        complaint_id=str(complaint["id"]),
        complaint_number=complaint["complaint_number"],
        reviewer=current_user,
        action=action,
        original_genai_value=original_genai,
        original_python_value=original_python,
        reviewer_final_value=reviewer_final,
        comment=body.comment or "",
    )

    return {
        "success": True,
        "action": action,
        "complaint_id": complaint["id"],
        "complaint_number": complaint["complaint_number"],
        "new_status": complaint.get("status"),
        "audit_entry_id": audit_entry["id"],
    }


# ── GET /reviewer/{complaint_id}/audit-trail ──────────────────────────────────

@router.get("/{complaint_id}/audit-trail")
def get_audit_trail(
    complaint_id: str,
    current_user: Dict[str, Any] = Depends(require_role("Reviewer", "Manager", "Admin", "Administrator")),
):
    """Returns the full immutable reviewer decision history for a complaint."""
    complaint = _find_complaint(complaint_id)
    cid = str(complaint["id"])
    cnum = complaint["complaint_number"]

    trail = [
        e for e in REVIEWER_DECISION_AUDIT
        if str(e.get("complaint_id")) == cid or e.get("complaint_number") == cnum
    ]
    trail.sort(key=lambda x: x["timestamp"])
    return {"complaint_id": cid, "complaint_number": cnum, "decisions": trail}
