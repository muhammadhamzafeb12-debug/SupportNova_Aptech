"""
Complaint Status State Machine — SupportNova
============================================
Enforces a strict directed-graph of valid complaint status transitions.
Any attempt to move to a status not reachable from the current one
will be rejected with a descriptive error — no free-form status writes.

Valid statuses and their allowed successors:
  New            → Analyzed
  Analyzed       → Assigned, Escalated
  Assigned       → In Progress, Escalated
  In Progress    → Awaiting Customer, Resolved, Escalated
  Awaiting Customer → In Progress, Escalated, Resolved
  Escalated      → In Progress, Resolved
  Resolved       → Closed
  Closed         → Reopened
  Reopened       → Assigned, In Progress, Escalated
"""
from typing import Dict, FrozenSet

# ── Graph definition ─────────────────────────────────────────────────────────

# Maps each status → set of statuses it can legally transition to.
VALID_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    "New":               frozenset({"Analyzed"}),
    "Analyzed":          frozenset({"Assigned", "Escalated"}),
    "Assigned":          frozenset({"In Progress", "Escalated"}),
    "In Progress":       frozenset({"Awaiting Customer", "Resolved", "Escalated"}),
    "Awaiting Customer": frozenset({"In Progress", "Escalated", "Resolved"}),
    "Escalated":         frozenset({"In Progress", "Resolved"}),
    "Resolved":          frozenset({"Closed"}),
    "Closed":            frozenset({"Reopened"}),
    "Reopened":          frozenset({"Assigned", "In Progress", "Escalated"}),
    # Legacy / transitional aliases kept for backward compat with seeded data.
    # They can only transition forward — not treated as a full node.
    "Submitted":         frozenset({"New", "Analyzed", "Assigned"}),
    "In Review":         frozenset({"Assigned", "In Progress", "Escalated"}),
    "Review Required":   frozenset({"Assigned", "In Progress", "Escalated"}),
}

ALL_KNOWN_STATUSES: FrozenSet[str] = frozenset(VALID_TRANSITIONS.keys())


def validate_transition(current_status: str, new_status: str) -> bool:
    """
    Pure function — returns True when the transition is valid, False otherwise.

    Args:
        current_status: The complaint's current status string.
        new_status:     The requested next status string.

    Returns:
        bool: True if the transition is permitted, False if it is forbidden
              or if either status is unrecognised.

    Note:
        No-op transitions (current == new) return True so that PATCH calls
        that don't change the status field still succeed.
    """
    if current_status == new_status:
        return True

    allowed = VALID_TRANSITIONS.get(current_status)
    if allowed is None:
        # Unknown source status — treat as unrecognised, disallow
        return False

    return new_status in allowed


def assert_valid_transition(current_status: str, new_status: str) -> None:
    """
    Raises ValueError with a human-readable message if the transition is
    invalid.  Use inside API endpoints to get the automatic 400 response.
    """
    if not validate_transition(current_status, new_status):
        raise ValueError(
            f"Invalid status transition: '{current_status}' → '{new_status}'. "
            f"Allowed next states from '{current_status}': "
            f"{sorted(VALID_TRANSITIONS.get(current_status, set()))}."
        )
