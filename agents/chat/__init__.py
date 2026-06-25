"""
agents/chat/__init__.py

ChatAgent — The MCP Client Orchestrator.
1. Takes a user message and session ID.
2. Loads session and conversation history from DB.
3. Asks Groq to pick a tool based on the history + message.
4. Executes the chosen tool.
5. Asks Groq to format the tool result into plain English (if applicable).
6. Saves everything to the database.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException
from groq import Groq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.chat.tools import market_data, text_to_sql
from config.settings import settings
from db.models.chat import ChatMessage, ChatSession
from services.v1.config.runtime_settings import runtime

logger = logging.getLogger(__name__)

MAX_HISTORY = 10
_PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class ChatResponse:
    session_id: str
    reply: str
    tool_used: str | None


def _load_prompt(name: str) -> str:
    """Load a prompt text file from the prompts directory."""
    try:
        return (_PROMPTS_DIR / f"chat_{name}.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback to backend/prompts if we couldn't find it in agents/chat/prompts
        # (Since I created them in backend/prompts in the previous steps)
        fallback = _PROMPTS_DIR.parent.parent.parent / "prompts" / f"chat_{name}.txt"
        return fallback.read_text(encoding="utf-8")


def _format_history(messages: list[ChatMessage]) -> str:
    """Format DB message models into a readable string for Groq prompt context."""
    if not messages:
        return "(no previous conversation)"
    lines = []
    for m in messages:
        role = "User" if m.role == "user" else "TradeBot"
        lines.append(f"[{role}]: {m.content}")
    return "\n".join(lines)


def _get_groq_client() -> Groq:
    groq_key = str(runtime.get("groq_key") or settings.GROQ_API_KEY).strip()
    if not groq_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    return Groq(api_key=groq_key)


async def _run_groq(system: str, user: str, json_mode: bool = False) -> str:
    """Helper to run Groq completion async."""
    client = _get_groq_client()
    kwargs = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "model": str(runtime.get("ai_model") or "llama-3.3-70b-versatile"),
        "temperature": 0.2,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await asyncio.to_thread(client.chat.completions.create, **kwargs)
    return response.choices[0].message.content.strip()


async def chat(user_message: str, session_id: str | None, user_id: str, db: AsyncSession) -> ChatResponse:
    """Main orchestrator for the Chat agent."""
    
    # ── 1. Resolve session ───────────────────────────────────────────────────
    if session_id:
        session = await db.get(ChatSession, session_id)
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=user_id)
        db.add(session)
        await db.flush()
        logger.info("[ChatAgent] Created new session: %s", session.id)

    # Capture as plain string immediately — accessing session.id after a rollback
    # would trigger a synchronous lazy-load which fails in async context.
    session_id = str(session.id)

    # ── 2. Load history ──────────────────────────────────────────────────────
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY)
    )
    result = await db.execute(stmt)
    # Reverse to chronological order
    history = list(result.scalars())[::-1]

    # ── 3. Save user message ─────────────────────────────────────────────────
    db.add(ChatMessage(session_id=session_id, role="user", content=user_message))
    if not session.title:
        session.title = user_message[:80]
        logger.info("[ChatAgent] Set session title to: %s", session.title)
        
    await db.commit()

    # ── 4. Pick Tool ─────────────────────────────────────────────────────────
    system_base = _load_prompt("system")
    router_prompt = (
        _load_prompt("tool_router")
        .replace("{{history}}", _format_history(history))
        .replace("{{user_message}}", user_message)
    )

    logger.info("[ChatAgent] Asking Groq to select a tool...")
    tool_json = await _run_groq(system=system_base, user=router_prompt, json_mode=True)
    
    try:
        tool_choice = json.loads(tool_json)
        tool_name = tool_choice.get("tool", "general_chat")
        tool_args = tool_choice.get("args", {})
    except json.JSONDecodeError:
        logger.warning("[ChatAgent] Failed to parse tool router JSON. Falling back to general_chat. Raw: %s", tool_json)
        tool_name = "general_chat"
        tool_args = {"message": user_message}

    logger.info("[ChatAgent] Selected tool: %s with args: %s", tool_name, tool_args)

    # ── 5. Execute Tool + Format Response ────────────────────────────────────
    raw_data = None
    reply = ""

    try:
        if tool_name == "text_to_sql":
            raw_data = await text_to_sql.text_to_sql(tool_args.get("question", user_message), db)
            formatter_user = (
                _load_prompt("response_formatter")
                .replace("{{history}}", _format_history(history))
                .replace("{{user_message}}", user_message)
                .replace("{{tool_name}}", tool_name)
                .replace("{{tool_output}}", json.dumps(raw_data, default=str))
            )
            reply = await _run_groq(system=system_base, user=formatter_user)

        elif tool_name == "market_data":
            raw_data = await market_data.market_data(tool_args.get("ticker", ""))
            formatter_user = (
                _load_prompt("response_formatter")
                .replace("{{history}}", _format_history(history))
                .replace("{{user_message}}", user_message)
                .replace("{{tool_name}}", tool_name)
                .replace("{{tool_output}}", json.dumps(raw_data, default=str))
            )
            reply = await _run_groq(system=system_base, user=formatter_user)

        else:
            # general_chat fallback
            tool_name = "general_chat"
            gen_system = _load_prompt("general")
            # For general chat, we pass history in the prompt manually since we don't have a specific formatter
            gen_prompt = f"Conversation history:\n{_format_history(history)}\n\nUser: {user_message}"
            reply = await _run_groq(system=gen_system, user=gen_prompt)

    except Exception as exc:
        logger.exception("[ChatAgent] Tool execution failed:")
        await db.rollback()
        reply = f"I'm sorry, I ran into an error while trying to answer that: {exc}"
        tool_name = "error"

    # ── 6. Save Assistant Reply ──────────────────────────────────────────────
    # Sanitise tool_output: SQL rows may contain datetime/Decimal objects that
    # are not JSON-serialisable by the default encoder. Round-trip through
    # json.dumps(default=str) converts them to strings so PostgreSQL JSON
    # columns can accept the value without errors.
    safe_output: dict | None = None
    if raw_data is not None:
        try:
            safe_output = json.loads(json.dumps(raw_data, default=str))
        except Exception:
            safe_output = {"error": "tool output could not be serialised"}

    db.add(
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content=reply,
            tool_used=tool_name,
            tool_input=tool_args,
            tool_output=safe_output,
        )
    )
    await db.commit()


    return ChatResponse(session_id=session_id, reply=reply, tool_used=tool_name)
