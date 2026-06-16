"""
signal_dto.py

Internal Data Transfer Object used when creating a Signal record.
This is NOT an API schema — it's used to pass parsed data between
the parsing layer and signal_service.create_signal().
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SignalDTO:
    """Carries the fields required to create a new Signal row."""
    ticker: str
    action: str                     # must match ActionType enum value
    entry_price: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    parent_signal_id: str | None = None
