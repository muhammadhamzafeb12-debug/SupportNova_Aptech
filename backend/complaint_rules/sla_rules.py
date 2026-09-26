"""
SLA Rules Engine for SupportNova Pipeline 2.
Calculates response deadlines, resolution deadlines, SLA risks, and SLA breaches.
"""

import datetime
from typing import Dict, Any, Tuple

SLA_MATRIX = {
    "P0 – Critical": {"response_hours": 1, "resolution_hours": 4},
    "P1 – High": {"response_hours": 4, "resolution_hours": 12},
    "P2 – Medium": {"response_hours": 12, "resolution_hours": 24},
    "P3 – Low": {"response_hours": 24, "resolution_hours": 48}
}

DEPARTMENT_SLA_OVERRIDES = {
    "Safety": 2,
    "Account Security": 6,
    "Compliance": 12,
    "Billing": 12,
    "Logistics": 24,
    "Returns": 24,
    "Warranty": 48,
    "Customer Relations": 24
}

def calculate_sla_deadlines(
    priority: str,
    department: str,
    submitted_at: datetime.datetime = None
) -> Tuple[int, datetime.datetime, datetime.datetime]:
    """
    Calculates expected SLA hours, response deadline, and resolution deadline.
    """
    if submitted_at is None:
        submitted_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    sla_info = SLA_MATRIX.get(priority, SLA_MATRIX["P3 – Low"])
    resolution_hours = DEPARTMENT_SLA_OVERRIDES.get(department, sla_info["resolution_hours"])
    response_hours = max(1, resolution_hours // 2)

    response_deadline = submitted_at + datetime.timedelta(hours=response_hours)
    resolution_deadline = submitted_at + datetime.timedelta(hours=resolution_hours)

    return resolution_hours, response_deadline, resolution_deadline

def check_sla_status(
    submitted_at: datetime.datetime,
    resolution_deadline: datetime.datetime,
    resolved_at: datetime.datetime = None
) -> str:
    """
    Returns SLA status: 'ON_TRACK', 'AT_RISK', or 'BREACHED'.
    """
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    if resolved_at:
        return "RESOLVED_ON_TIME" if resolved_at <= resolution_deadline else "BREACHED"

    if now > resolution_deadline:
        return "BREACHED"
    
    time_remaining = resolution_deadline - now
    if time_remaining.total_seconds() <= 7200:  # Less than 2 hours remaining
        return "AT_RISK"

    return "ON_TRACK"
