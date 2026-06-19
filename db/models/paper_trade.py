"""
paper_trade.py

Records every paper trade executed by the system.
One row per bracket order — tracks entry, TP target, SL target,
validation snapshot (EMA/VWAP at time of entry), and final P&L.
"""
from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ExitReason(str, enum.Enum):
    TP_HIT = "TP_HIT"       # take-profit triggered
    SL_HIT = "SL_HIT"       # stop-loss triggered
    MANUAL = "MANUAL"        # manually closed


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    # ── Identity ────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    parsed_signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parsed_signals.id"), nullable=False, index=True,
    )

    # ── Broker info ──────────────────────────────────────────
    broker: Mapped[str] = mapped_column(String(32), nullable=False)          # "alpaca" | "webull"
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # ── Instrument ──────────────────────────────────────────
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Prices ──────────────────────────────────────────────
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss_price: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Exit (filled in when trade closes) ──────────────────
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_reason: Mapped[ExitReason | None] = mapped_column(SAEnum(ExitReason), nullable=True)
    pnl_pct: Mapped[float | None] = mapped_column(Float, nullable=True)        # e.g. 15.0 for +15%
    pnl_dollars: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Status ──────────────────────────────────────────────
    status: Mapped[TradeStatus] = mapped_column(
        SAEnum(TradeStatus), default=TradeStatus.OPEN, nullable=False, index=True,
    )

    # ── Validation snapshot ──────────────────────────────────
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ema9: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema13: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema21: Mapped[float | None] = mapped_column(Float, nullable=True)
    vwap: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ──────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
