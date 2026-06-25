"""
agents/chat/tools/market_data.py

Tool 2 — Market Data

Wraps existing yfinance + EMA/VWAP validator to return live price and
trend data for a given ticker. Zero new infrastructure — reuses what's
already in the codebase.
"""
from __future__ import annotations

import logging

from services.v1.market_data.factory import get_market_data
from services.v1.validation.ema_vwap_validator import validate

logger = logging.getLogger(__name__)


async def market_data(ticker: str) -> dict:
    """
    Fetch live price and EMA/VWAP snapshot for a stock ticker.

    Returns a JSON-serialisable dict with all indicator values and a
    human-readable summary of whether the trend is valid.
    """
    ticker = ticker.upper().strip()
    logger.info("[ChatTool/market_data] Fetching data for %s", ticker)

    md = get_market_data()
    try:
        price = await md.get_current_price(ticker)
    except Exception as exc:
        logger.warning("[ChatTool/market_data] Price fetch failed for %s: %s", ticker, exc)
        price = None

    validation = await validate(ticker)

    return {
        "ticker": ticker,
        "live_price": price,
        "ema9": validation.ema9,
        "ema13": validation.ema13,
        "ema21": validation.ema21,
        "vwap": validation.vwap,
        "trend_valid": validation.passed,
        "summary": validation.reason,
    }
