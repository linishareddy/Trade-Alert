"""
signal_controller.py

Orchestrates listing and fetching ParsedSignal records for the API layer.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.v1.signals import SignalOut, SignalListOut
from services.v1.signals import signal_service


def _to_schema(signal) -> SignalOut:
    return SignalOut(
        id=signal.id,
        raw_alert_id=signal.raw_alert_id,
        action=signal.action.value,
        status=signal.status.value,
        ticker=signal.ticker,
        contract_type=signal.contract_type.value,
        strike=signal.strike,
        expiry=signal.expiry,
        entry_price=signal.entry_price,
        target_price=signal.target_price,
        stop_loss=signal.stop_loss,
        parse_format=signal.parse_format,
        parent_id=signal.parent_id,
        created_at=signal.created_at.isoformat(),
        updated_at=signal.updated_at.isoformat(),
    )


async def list_signals(
    db: AsyncSession,
    ticker: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> SignalListOut:
    total, signals = await signal_service.list_signals(db, ticker, status, limit, offset)
    return SignalListOut(
        total=total,
        signals=[_to_schema(s) for s in signals],
    )


async def get_signal(db: AsyncSession, signal_id: str) -> SignalOut | None:
    signal = await signal_service.get_signal_by_id(db, signal_id)
    if not signal:
        return None
    return _to_schema(signal)
