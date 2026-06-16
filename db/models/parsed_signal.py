"""
parsed_signal.py

Options-aware signal model. This is the authoritative parsed output
from the Parsing Agent. Replaces the older `signals` table.
"""
from __future__ import annotations
import uuid
import enum
from datetime import datetime, date, timezone
from sqlalchemy import String, Float, Date, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base


class ActionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"
    EXIT = "EXIT"
    SL_HIT = "SL_HIT"
    UPDATE = "UPDATE"


class ContractType(str, enum.Enum):
    CALL = "CALL"
    PUT = "PUT"
    STOCK = "STOCK"
    UNKNOWN = "UNKNOWN"


class SignalStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"


class ParsedSignal(Base):
    __tablename__ = "parsed_signals"

    # ── Identity ────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    raw_alert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("raw_alerts.id"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("parsed_signals.id"), nullable=True
    )

    # ── Core intent ─────────────────────────────────────────
    action: Mapped[ActionType] = mapped_column(
        SAEnum(ActionType), nullable=False, index=True
    )
    status: Mapped[SignalStatus] = mapped_column(
        SAEnum(SignalStatus), default=SignalStatus.OPEN, nullable=False
    )

    # ── Instrument ──────────────────────────────────────────
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    contract_type: Mapped[ContractType] = mapped_column(
        SAEnum(ContractType), default=ContractType.UNKNOWN, nullable=False
    )
    strike: Mapped[float | None] = mapped_column(Float, nullable=True)
    expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Pricing ─────────────────────────────────────────────
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Parse audit ─────────────────────────────────────────
    # Which of the 3 known formats matched: "A", "B", "C", or "UNKNOWN"
    parse_format: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)

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

    # ── Relationships ────────────────────────────────────────
    # Self-referential: a follow-up ParsedSignal points to its parent
    children: Mapped[list["ParsedSignal"]] = relationship(
        "ParsedSignal",
        foreign_keys="ParsedSignal.parent_id",
        back_populates="parent",
        lazy="select",
    )
    parent: Mapped["ParsedSignal | None"] = relationship(
        "ParsedSignal",
        foreign_keys="ParsedSignal.parent_id",
        back_populates="children",
        remote_side="ParsedSignal.id",
        lazy="select",
    )
