"""
Broker-agnostic data models.
These are the ONLY types the execution agent and monitor ever touch.
No broker SDK types leak beyond the adapter files.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class BracketOrderRequest:
    """Everything a broker needs to open a position with automatic TP + SL."""
    symbol: str
    qty: int
    side: str                    # "buy" | "sell"
    take_profit_pct: float       # e.g. 0.15 for 15%
    stop_loss_pct: float         # e.g. 0.10 for 10%
    entry_price: float           # live price used for TP/SL calculation


@dataclass
class BrokerOrderResult:
    """Normalised response returned by every broker adapter."""
    broker_order_id: str
    symbol: str
    qty: int
    filled_avg_price: float | None
    status: str                  # "submitted" | "filled" | "failed"
    raw_response: dict = field(default_factory=dict)


@dataclass
class Position:
    """A currently open position as reported by the broker."""
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl_pct: float   # e.g. 0.05 for +5%
    broker_order_id: str
