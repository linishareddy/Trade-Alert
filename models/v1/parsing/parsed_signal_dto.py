"""
parsed_signal_dto.py

Internal DTO for data transfer between the Parsing Agent and the
service/DB layer. Not returned from any router directly.
"""
from __future__ import annotations
from datetime import date
from pydantic import BaseModel


class ParsedSignalDTO(BaseModel):
    """Internal DTO — never returned directly from a router."""

    # Core
    action: str                         # ActionType value e.g. "BUY", "EXIT"
    ticker: str                         # e.g. "SBUX", "SPXW", "QQQ"

    # Options
    contract_type: str = "UNKNOWN"      # "CALL", "PUT", "STOCK", "UNKNOWN"
    strike: float | None = None
    expiry: date | None = None

    # Pricing
    entry_price: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None

    # Lifecycle
    is_followup: bool = False           # True for EXIT, SL_HIT, SCALE_IN/OUT
    parent_id: str | None = None        # Linked to open ParsedSignal.id

    # Audit
    parse_format: str = "UNKNOWN"       # "A", "B", "C", or "UNKNOWN"
