"""
order.py

Tracks every order submitted to Webull — both successful placements
and failures. Each row links back to the ParsedSignal that triggered it.
"""
from __future__ import annotations
import uuid
import enum
from datetime import datetime, date, timezone
from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base


class InstrumentType(str, enum.Enum):
    EQUITY = "EQUITY"
    OPTIONS = "OPTIONS"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"       # Created locally, not yet sent
    SUBMITTED = "SUBMITTED"   # Accepted by Webull
    FILLED = "FILLED"         # Fully filled
    PARTIAL = "PARTIAL"       # Partially filled
    CANCELLED = "CANCELLED"   # Cancelled
    FAILED = "FAILED"         # Webull rejected / error


class WebullOrder(Base):
    __tablename__ = "webull_orders"

    # ── Identity ────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    parsed_signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parsed_signals.id"), nullable=False, index=True
    )

    # ── Webull account ───────────────────────────────────────
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    client_order_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True,
        default=lambda: str(uuid.uuid4())
    )

    # ── Instrument ──────────────────────────────────────────
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    instrument_type: Mapped[InstrumentType] = mapped_column(
        SAEnum(InstrumentType), nullable=False
    )

    # Options-specific (null for EQUITY)
    option_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    strike: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(8), nullable=True)  # "CALL" | "PUT"

    # ── Order params ─────────────────────────────────────────
    side: Mapped[OrderSide] = mapped_column(SAEnum(OrderSide), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(SAEnum(OrderType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Webull response ──────────────────────────────────────
    webull_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Raw API response (for debugging) ────────────────────
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ──────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
