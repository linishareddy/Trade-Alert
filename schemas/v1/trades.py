from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class PaperTradeResponse(BaseModel):
    id: str
    parsed_signal_id: str
    broker: str
    broker_order_id: str | None
    symbol: str
    qty: int
    entry_price: float
    take_profit_price: float
    stop_loss_price: float
    exit_price: float | None
    exit_reason: str | None
    pnl_pct: float | None
    pnl_dollars: float | None
    status: str
    validation_passed: bool
    ema9: float | None
    ema13: float | None
    ema21: float | None
    vwap: float | None
    validation_reason: str | None
    created_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    total: int
    trades: list[PaperTradeResponse]


class TradeSummaryResponse(BaseModel):
    total_trades: int
    open_trades: int
    closed_trades: int
    avg_pnl_pct: float | None
    total_pnl_dollars: float | None
