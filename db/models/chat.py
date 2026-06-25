"""
db/models/chat.py

Two tables that power the chatbot multi-session system:
  - ChatSession  — one row per conversation thread (scoped to a user)
  - ChatMessage  — one row per message turn (user or assistant)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    # Auto-set from the first message text (truncated to 80 chars)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )
    # Updated on every new message — used to sort sessions by recency
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    # 'user' or 'assistant'
    role: Mapped[str] = mapped_column(String(9), nullable=False)
    # The full text of the message or bot reply
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Populated only on assistant messages
    # 'text_to_sql' | 'market_data' | 'general_chat'
    tool_used: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Args sent to the tool e.g. {"question": "best win rate?"}
    tool_input: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Raw result from the tool before formatting — useful for debugging
    tool_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )

    session: Mapped["ChatSession"] = relationship(
        "ChatSession", back_populates="messages"
    )
