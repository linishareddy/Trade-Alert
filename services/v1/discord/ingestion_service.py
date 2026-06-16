"""
ingestion_service.py

Orchestrates the full ingest pipeline:
1. Deduplicate — skip already-seen message_ids
2. Save raw alert to DB (raw_alerts table)
3. Parse via ParsingAgent (regex, no LLM)
4. Match follow-up messages to their parent ParsedSignal
5. Persist ParsedSignal to parsed_signals table
6. Auto-execute via Webull (if WEBULL_EXECUTION_ENABLED=true)
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from db.models.raw_alert import RawAlert
from db.models.parsed_signal import ParsedSignal, SignalStatus, ActionType
from schemas.v1.ingest import RawAlertIn
import agents.parsing as parsing_agent


# Actions that represent a follow-up on an existing open signal
_FOLLOWUP_ACTIONS = {
    ActionType.EXIT,
    ActionType.SL_HIT,
    ActionType.SCALE_IN,
    ActionType.SCALE_OUT,
    ActionType.HOLD,
    ActionType.UPDATE,
}

# Status transitions triggered by follow-up actions
_STATUS_ON_ACTION: dict[ActionType, SignalStatus] = {
    ActionType.EXIT: SignalStatus.CLOSED,
    ActionType.SL_HIT: SignalStatus.CLOSED,
    ActionType.SCALE_IN: SignalStatus.PARTIAL,
    ActionType.SCALE_OUT: SignalStatus.PARTIAL,
}


async def _find_parent(
    db: AsyncSession, ticker: str, lookback_hours: int = 72
) -> ParsedSignal | None:
    """Return the most recent OPEN or PARTIAL ParsedSignal for this ticker."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.ticker == ticker.upper(),
            ParsedSignal.status.in_([SignalStatus.OPEN, SignalStatus.PARTIAL]),
            ParsedSignal.created_at >= cutoff,
        ).order_by(ParsedSignal.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


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
    raw = existing.scalar_one_or_none()

    if raw and not alert.is_edit:
        return False, None  # Already processed, skip

    if raw and alert.is_edit:
        raw.content = alert.content
        raw.embeds = alert.embeds
        raw.is_edit = True
        await db.commit()
        await db.refresh(raw)
    else:
        # ── 2. Persist raw alert ─────────────────────────────
        raw = RawAlert(
            message_id=alert.message_id,
            channel_id=alert.channel_id,
            author=alert.author,
            content=alert.content,
            embeds=alert.embeds,
            is_edit=alert.is_edit,
        )
        db.add(raw)
        await db.commit()
        await db.refresh(raw)

    # ── 3. Parse via ParsingAgent ────────────────────────────
    dto = parsing_agent.parse(alert.content, alert.embeds)
    if not dto:
        return True, None  # Saved to raw_alerts but no recognised signal format

    # ── 4. Match follow-ups to parent ────────────────────────
    parent_id: str | None = None
    action_enum = ActionType(dto.action)

    if action_enum in _FOLLOWUP_ACTIONS:
        parent = await _find_parent(db, dto.ticker)
        if parent:
            parent_id = parent.id
            new_status = _STATUS_ON_ACTION.get(action_enum)
            if new_status:
                parent.status = new_status
                parent.updated_at = datetime.now(timezone.utc)
                await db.commit()

    # ── 5. Persist ParsedSignal ──────────────────────────────
    signal = ParsedSignal(
        raw_alert_id=raw.id,
        parent_id=parent_id,
        action=action_enum,
        status=SignalStatus.OPEN,
        ticker=dto.ticker,
        contract_type=dto.contract_type,
        strike=dto.strike,
        expiry=dto.expiry,
        entry_price=dto.entry_price,
        target_price=dto.target_price,
        stop_loss=dto.stop_loss,
        parse_format=dto.parse_format,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    # ── 6. Auto-execute via Webull ───────────────────────────
    import agents.execution as execution_agent
    await execution_agent.execute(signal, db)

    return True, signal
