"""
routers/v1/chat.py

Endpoints for the MCP trading chatbot.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.chat import chat
from db.models.chat import ChatMessage, ChatSession
from db.models.user import User
from routers.v1.auth import get_current_user
from db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    session_id: str | None = None


class RenameSessionRequest(BaseModel):
    title: str = Field(..., max_length=100)


class ChatResponseDTO(BaseModel):
    session_id: str
    reply: str
    tool_used: str | None


class SessionListDTO(BaseModel):
    id: str
    title: str | None
    created_at: Any
    last_message_at: Any


class MessageDTO(BaseModel):
    id: str
    role: str
    content: str
    tool_used: str | None
    created_at: Any


@router.post("", response_model=ChatResponseDTO)
async def chat_endpoint(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the SentinelAI.
    If session_id is omitted, a new chat session is created.
    """
    logger.info("[Router/Chat] User %s asked: %s (session=%s)", current_user.email, body.message[:50], body.session_id)
    result = await chat(body.message, body.session_id, current_user.id, db)
    return ChatResponseDTO(
        session_id=result.session_id,
        reply=result.reply,
        tool_used=result.tool_used,
    )


@router.get("/sessions", response_model=list[SessionListDTO])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chat sessions for the authenticated user, sorted by recent activity."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.last_message_at.desc())
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    return [
        SessionListDTO(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            last_message_at=s.last_message_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageDTO])
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full message history for a specific chat session."""
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        MessageDTO(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_used=m.tool_used,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.put("/sessions/{session_id}", response_model=SessionListDTO)
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rename a specific chat session."""
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = body.title
    await db.commit()
    await db.refresh(session)

    return SessionListDTO(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific chat session and all its messages."""
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"status": "ok"}

