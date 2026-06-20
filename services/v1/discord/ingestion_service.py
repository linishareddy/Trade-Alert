"""
ingestion_service.py

Orchestrates the full ingest pipeline:
1. Deduplicate — skip already-seen message_ids
2. Save raw alert to DB (raw_alerts table)
3. Forward raw Discord text to WhatsApp (when enabled)
4. Parse via ParsingAgent (regex first, Groq AI fallback)
5. Match follow-up messages to their parent ParsedSignal
6. Persist ParsedSignal to parsed_signals table
7. Auto-execute via ExecutionAgent (if EXECUTION_ENABLED=true)
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models.raw_alert import RawAlert
from db.models.parsed_signal import ParsedSignal, SignalStatus, ActionType, ContractType
from schemas.v1.ingest import RawAlertIn
import agents.parsing as parsing_agent
import agents.execution as execution_agent

logger = logging.getLogger(__name__)

_FOLLOWUP_ACTIONS = {
    ActionType.EXIT,
    ActionType.SL_HIT,
    ActionType.SCALE_IN,
    ActionType.SCALE_OUT,
    ActionType.HOLD,
    ActionType.UPDATE,
}

_STATUS_ON_ACTION: dict[ActionType, SignalStatus] = {
    ActionType.EXIT: SignalStatus.CLOSED,
    ActionType.SL_HIT: SignalStatus.CLOSED,
    ActionType.SCALE_IN: SignalStatus.PARTIAL,
    ActionType.SCALE_OUT: SignalStatus.PARTIAL,
}


async def _find_parent(
    db: AsyncSession, ticker: str, lookback_hours: int = 72
) -> ParsedSignal | None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.ticker == ticker.upper(),
            ParsedSignal.status.in_([SignalStatus.OPEN, SignalStatus.PARTIAL]),
            ParsedSignal.created_at >= cutoff,
        ).order_by(ParsedSignal.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


def _discord_message_text(content: str, embeds: list) -> str:
    if content.strip():
        return content.strip()
    if embeds:
        lines: list[str] = []
        for embed in embeds:
            title = (embed.get("title") or "").strip()
            if title:
                lines.append(title)
            for field in embed.get("fields", []):
                name = (field.get("name") or "").strip()
                value = (field.get("value") or "").strip()
                if name or value:
                    lines.append(f"{name}: {value}".strip(": "))
        if lines:
            return "\n".join(lines)
    return "[Empty Discord message]"


async def ingest_alert(
    db: AsyncSession, alert: RawAlertIn
) -> tuple[bool, ParsedSignal | None]:
    """
    Main ingest entry point.
    Returns (accepted: bool, parsed_signal: ParsedSignal | None).
    """

    # ── 1. Deduplicate ───────────────────────────────────────
    existing = await db.execute(
        select(RawAlert).where(RawAlert.message_id == alert.message_id)
    )
    if existing.scalar_one_or_none():
        print(f"[Ingest] Duplicate skipped — message_id={alert.message_id}")
        return False, None

    # ── 2. Save raw alert ────────────────────────────────────
    raw = RawAlert(
        message_id=alert.message_id,
        channel_id=alert.channel_id,
        author=alert.author,
        content=alert.content,
        embeds=alert.embeds,
        is_edit=alert.is_edit,
    )
    db.add(raw)
    await db.flush()  # assign raw.id without full commit

    text = _discord_message_text(alert.content, alert.embeds)
    print(f"[Ingest] New Discord message from {alert.author}: {text[:100]}")

    from services.v1.notifications.whatsapp_service import notify_discord_message
    wa_ok = await notify_discord_message(text)
    print(f"[Ingest] WhatsApp forward: {'✅ sent' if wa_ok else '❌ not sent (check toggle + Twilio)'}")

    # ── 3. Parse ─────────────────────────────────────────────
    dto = await parsing_agent.parse_async(alert.content, alert.embeds)
    if not dto:
        logger.warning("[Ingest] No format matched for message: %r", alert.content[:120])
        await db.commit()  # save the raw alert even if unparseable
        return True, None

    logger.info(
        "[Ingest] Parsed: action=%s ticker=%s format=%s entry=%s",
        dto.action, dto.ticker, dto.parse_format, dto.entry_price,
    )

    # ── 4. Match follow-ups to parent ────────────────────────
    parent_id: str | None = None
    if dto.is_followup:
        parent = await _find_parent(db, dto.ticker)
        if parent:
            parent_id = parent.id
            new_status = _STATUS_ON_ACTION.get(ActionType(dto.action), parent.status)
            parent.status = new_status
            parent.updated_at = datetime.now(timezone.utc)
            logger.info(
                "[Ingest] Linked follow-up %s to parent %s → status=%s",
                dto.action, parent_id, new_status.value,
            )

    # ── 5. Persist ParsedSignal ──────────────────────────────
    signal = ParsedSignal(
        raw_alert_id=raw.id,
        parent_id=parent_id,
        action=ActionType(dto.action),
        ticker=dto.ticker.upper(),
        contract_type=ContractType(dto.contract_type) if dto.contract_type else ContractType.UNKNOWN,
        strike=dto.strike,
        expiry=dto.expiry,
        entry_price=dto.entry_price,
        target_price=dto.target_price,
        stop_loss=dto.stop_loss,
        parse_format=dto.parse_format,
        status=SignalStatus.OPEN,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    # ── 6. Execute (entry signals only) ─────────────────────
    if not dto.is_followup:
        await execution_agent.execute(signal, db)

    return True, signal
