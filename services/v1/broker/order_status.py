"""
Classify broker order status strings (Alpaca-compatible).

Used by the monitor agent to avoid closing trades while the entry order
is still pending (e.g. market closed, not yet filled).
"""
from __future__ import annotations
from typing import Literal

OrderPhase = Literal["pending", "filled", "cancelled", "unknown"]

# Entry not yet executed — do NOT treat as a closed position.
_PENDING = frozenset({
    "new",
    "accepted",
    "pending_new",
    "accepted_for_bidding",
    "pending_cancel",
    "pending_replace",
    "partially_filled",
    "done_for_day",
    "stopped",
    "suspended",
    "calculated",
})

# Entry will never fill — safe to mark trade CANCELLED in DB.
_TERMINAL_UNFILLED = frozenset({
    "canceled",
    "cancelled",
    "expired",
    "rejected",
    "replaced",
})

_FILLED = frozenset({"filled"})


def classify_order_status(status: str) -> OrderPhase:
    """Map a broker order status string to a coarse lifecycle phase."""
    normalized = status.strip().lower().replace("-", "_")
    if normalized in _PENDING:
        return "pending"
    if normalized in _TERMINAL_UNFILLED:
        return "cancelled"
    if normalized in _FILLED:
        return "filled"
    return "unknown"
