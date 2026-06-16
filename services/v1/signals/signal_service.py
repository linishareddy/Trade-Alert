"""
signal_service.py

DB access for ParsedSignal records (the new parsed_signals table).
The old Signal model (signals table) is kept for data-preservation only.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.parsed_signal import ParsedSignal, ActionType, SignalStatus


async def get_open_signals_for_ticker(
    db: AsyncSession, ticker: str, lookback_hours: int = 72
) -> list[ParsedSignal]:
    """Return OPEN/PARTIAL ParsedSignals for a ticker within the lookback window."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.ticker == ticker.upper(),
            ParsedSignal.status.in_([SignalStatus.OPEN, SignalStatus.PARTIAL]),
            ParsedSignal.created_at >= cutoff,
        ).order_by(ParsedSignal.created_at.desc())
    )
    return list(result.scalars().all())


async def update_signal_status(
    db: AsyncSession, signal_id: str, status: SignalStatus
) -> ParsedSignal | None:
    """Update a signal's status. Returns None if not found."""
    result = await db.execute(select(ParsedSignal).where(ParsedSignal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        return None
    signal.status = status
    signal.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(signal)
    return signal


async def list_signals(
    db: AsyncSession,
    ticker: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[ParsedSignal]]:
    """Return (total_count, page_of_parsed_signals)."""
    base = select(ParsedSignal)
    if ticker:
        base = base.where(ParsedSignal.ticker == ticker.upper())
    if status:
        base = base.where(ParsedSignal.status == SignalStatus(status))

    count_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(ParsedSignal.created_at.desc()).limit(limit).offset(offset)
    )
    return total, list(result.scalars().all())


async def get_signal_by_id(
    db: AsyncSession, signal_id: str
) -> ParsedSignal | None:
    result = await db.execute(select(ParsedSignal).where(ParsedSignal.id == signal_id))
    return result.scalar_one_or_none()
