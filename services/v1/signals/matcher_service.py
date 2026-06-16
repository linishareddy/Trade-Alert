"""
matcher_service.py

Maps follow-up Discord messages back to their original open Signal.
Uses rapidfuzz for loose ticker matching.
"""
from __future__ import annotations
from rapidfuzz import process, fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.signal import Signal
from services.v1.signals import signal_service


async def find_parent_signal(db: AsyncSession, ticker: str) -> Signal | None:
    """
    Given a ticker from a follow-up message, find the most recent
    OPEN or PARTIAL signal for that ticker within the last 72 hours.
    Uses rapidfuzz to handle minor ticker mismatches.
    """
    candidates = await signal_service.get_open_signals_for_ticker(db, ticker)
    if not candidates:
        # Try fuzzy match across recent open signals
        candidates = await signal_service.get_open_signals_for_ticker(db, ticker, lookback_hours=168)
        if not candidates:
            return None
        
        tickers = [s.ticker for s in candidates]
        match = process.extractOne(ticker.upper(), tickers, scorer=fuzz.WRatio, score_cutoff=80)
        if match:
            matched_ticker = match[0]
            candidates = [s for s in candidates if s.ticker == matched_ticker]
        else:
            return None

    # Return the most recently created open signal
    return candidates[0]
