from __future__ import annotations
from datetime import date
from pydantic import BaseModel


class SignalOut(BaseModel):
    """Response schema for a parsed trading signal."""
    id: str
    raw_alert_id: str

    # Core
    action: str
    status: str
    ticker: str

    # Options fields
    contract_type: str
    strike: float | None = None
    expiry: date | None = None

    # Pricing
    entry_price: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None

    # Audit
    parse_format: str
    parent_id: str | None = None

    created_at: str
    updated_at: str


class SignalListOut(BaseModel):
    """Paginated list of signals."""
    total: int
    signals: list[SignalOut]
