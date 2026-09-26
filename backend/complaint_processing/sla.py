"""
SLA Tracking Engine — SupportNova
===================================
Config-driven SLA targets per priority (P0/P1/P2/P3).
Targets stored in config/sla_targets.json — admin-editable at runtime.

compute_sla_status() is a pure function: no DB side-effects, easy to unit-test.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# ── Default SLA targets (also written to config file on first boot) ───────────
DEFAULT_SLA_TARGETS: Dict[str, Dict[str, Any]] = {
    "P0": {
        "label": "Critical",
        "response_time_hours": 2,
        "resolution_time_hours": 12,
        "at_risk_threshold_pct": 20,
    },
    "P1": {
        "label": "High",
        "response_time_hours": 4,
        "resolution_time_hours": 24,
        "at_risk_threshold_pct": 20,
    },
    "P2": {
        "label": "Medium",
        "response_time_hours": 8,
        "resolution_time_hours": 48,
        "at_risk_threshold_pct": 20,
    },
    "P3": {
        "label": "Low",
        "response_time_hours": 24,
        "resolution_time_hours": 72,
        "at_risk_threshold_pct": 20,
    },
}

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "sla_targets.json"


def _load_sla_targets() -> Dict[str, Dict[str, Any]]:
    """Load SLA targets from config file; fall back to defaults if absent/corrupt."""
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and len(data) > 0:
                return data
        except Exception:
            pass
    # Write defaults to disk so admin can edit them later
    _save_sla_targets(DEFAULT_SLA_TARGETS)
    return DEFAULT_SLA_TARGETS


def _save_sla_targets(targets: Dict[str, Dict[str, Any]]) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(targets, fh, indent=2)


def get_sla_targets() -> Dict[str, Dict[str, Any]]:
    return _load_sla_targets()


def update_sla_targets(new_targets: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    _save_sla_targets(new_targets)
    return new_targets


# ── Core SLA computation ──────────────────────────────────────────────────────

class SLAStatus:
    """Immutable result value returned by compute_sla_status()."""

    __slots__ = (
        "priority",
        "resolution_deadline_hours",
        "hours_elapsed",
        "time_remaining_hours",
        "is_at_risk",
        "is_breached",
        "at_risk_threshold_pct",
    )

    def __init__(
        self,
        priority: str,
        resolution_deadline_hours: float,
        hours_elapsed: float,
        time_remaining_hours: float,
        is_at_risk: bool,
        is_breached: bool,
        at_risk_threshold_pct: float,
    ):
        self.priority = priority
        self.resolution_deadline_hours = resolution_deadline_hours
        self.hours_elapsed = hours_elapsed
        self.time_remaining_hours = time_remaining_hours
        self.is_at_risk = is_at_risk
        self.is_breached = is_breached
        self.at_risk_threshold_pct = at_risk_threshold_pct

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority": self.priority,
            "resolution_deadline_hours": self.resolution_deadline_hours,
            "hours_elapsed": round(self.hours_elapsed, 2),
            "time_remaining_hours": round(self.time_remaining_hours, 2),
            "is_at_risk": self.is_at_risk,
            "is_breached": self.is_breached,
            "at_risk_threshold_pct": self.at_risk_threshold_pct,
        }


def _map_priority_to_tier(priority_str: str) -> str:
    """Normalise complaint priority field → P0/P1/P2/P3."""
    p = priority_str.upper().strip()
    mapping = {
        "P0": "P0", "CRITICAL": "P0", "URGENT": "P0",
        "P1": "P1", "HIGH": "P1",
        "P2": "P2", "MEDIUM": "P2", "NORMAL": "P2",
        "P3": "P3", "LOW": "P3",
    }
    # Accept "P0 – Critical" style
    for key, val in mapping.items():
        if p.startswith(key):
            return val
    return "P2"  # Default: medium


def compute_sla_status(
    complaint: Dict[str, Any],
    _now: Optional[datetime] = None,
    sla_targets: Optional[Dict[str, Dict[str, Any]]] = None,
) -> SLAStatus:
    """
    Pure function — computes SLA status for a single complaint dict.

    Args:
        complaint:   Complaint dict (must have 'priority' and 'created_at').
        _now:        Override for current time (used in unit tests to mock timestamps).
        sla_targets: Override SLA targets (used in unit tests).

    Returns:
        SLAStatus dataclass with time_remaining_hours, is_at_risk, is_breached.
    """
    targets = sla_targets if sla_targets is not None else _load_sla_targets()

    tier = _map_priority_to_tier(complaint.get("priority", "Medium"))
    tier_config = targets.get(tier, targets.get("P2", DEFAULT_SLA_TARGETS["P2"]))

    resolution_hours = float(tier_config.get("resolution_time_hours", 48))
    at_risk_pct = float(tier_config.get("at_risk_threshold_pct", 20)) / 100.0

    # Parse created_at
    created_raw = complaint.get("created_at")
    if isinstance(created_raw, str):
        try:
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except ValueError:
            created_at = datetime.now(timezone.utc)
    elif isinstance(created_raw, datetime):
        created_at = created_raw
    else:
        created_at = datetime.now(timezone.utc)

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    now = _now if _now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    hours_elapsed = (now - created_at).total_seconds() / 3600.0
    time_remaining = resolution_hours - hours_elapsed
    is_breached = time_remaining <= 0
    # at-risk: within (threshold_pct * total deadline) of the deadline
    at_risk_window = resolution_hours * at_risk_pct
    is_at_risk = (not is_breached) and (time_remaining <= at_risk_window)

    return SLAStatus(
        priority=tier,
        resolution_deadline_hours=resolution_hours,
        hours_elapsed=hours_elapsed,
        time_remaining_hours=time_remaining,
        is_at_risk=is_at_risk,
        is_breached=is_breached,
        at_risk_threshold_pct=at_risk_pct * 100,
    )


# ── Follow-up record helpers ──────────────────────────────────────────────────

FOLLOW_UP_TYPES = frozenset({
    "info_request",
    "resolution_confirmation",
    "refund_status",
    "replacement_status",
    "escalation_ack",
    "closure_confirmation",
})
