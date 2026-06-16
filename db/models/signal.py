import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base
import enum


class ActionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    SCALE = "SCALE"
    EXIT = "EXIT"
    SL_HIT = "SL_HIT"
    UPDATE = "UPDATE"


class SignalStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("raw_alerts.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    action: Mapped[ActionType] = mapped_column(SAEnum(ActionType), nullable=False)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[SignalStatus] = mapped_column(SAEnum(SignalStatus), default=SignalStatus.OPEN)
    parent_signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("signals.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
