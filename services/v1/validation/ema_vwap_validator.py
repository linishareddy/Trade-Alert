"""
EMA/VWAP Validator

Before executing any trade, this gate checks:
  price > EMA9  AND  price > EMA13  AND  price > EMA21  AND  price > VWAP

All four must pass — the same rule you see on the GOOGL chart:
price is above the dark VWAP line and all three short-term EMA lines.

Returns a ValidationResult with the snapshot values stored for the DB.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from services.v1.market_data.factory import get_market_data
from services.v1.market_data.models import OHLCVBar

logger = logging.getLogger(__name__)

MIN_BARS_REQUIRED = 21  # need at least 21 bars to compute EMA21


@dataclass
class ValidationResult:
    passed: bool
    current_price: float
    ema9: float
    ema13: float
    ema21: float
    vwap: float
    reason: str


# ── Math helpers ──────────────────────────────────────────────────────────────

def _ema(closes: list[float], period: int) -> float:
    """Exponential moving average over a list of closes."""
    if len(closes) < period:
        return closes[-1]
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period   # seed with SMA
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def _vwap(bars: list[OHLCVBar]) -> float:
    """Volume-weighted average price for the given bars (intraday session)."""
    cum_tp_vol = 0.0
    cum_vol = 0.0
    for b in bars:
        typical = (b.high + b.low + b.close) / 3.0
        cum_tp_vol += typical * b.volume
        cum_vol += b.volume
    if cum_vol == 0:
        return bars[-1].close
    return cum_tp_vol / cum_vol


# ── Public entry point ────────────────────────────────────────────────────────

async def validate(symbol: str) -> ValidationResult:
    """
    Fetch live bars, compute EMA9/13/21 and VWAP, check if price is above all.
    Returns ValidationResult — caller decides whether to proceed with trade.
    """
    md = get_market_data()

    bars, current_price = await _fetch(md, symbol)

    if len(bars) < MIN_BARS_REQUIRED:
        msg = f"Only {len(bars)} bars available, need {MIN_BARS_REQUIRED}"
        logger.warning("[Validator] %s — %s", symbol, msg)
        return ValidationResult(
            passed=False,
            current_price=current_price,
            ema9=0.0, ema13=0.0, ema21=0.0, vwap=0.0,
            reason=msg,
        )

    closes = [b.close for b in bars]
    ema9  = _ema(closes, 9)
    ema13 = _ema(closes, 13)
    ema21 = _ema(closes, 21)
    vwap  = _vwap(bars)

    checks: dict[str, bool] = {
        f"price({current_price:.2f}) > EMA9({ema9:.2f})":   current_price > ema9,
        f"price({current_price:.2f}) > EMA13({ema13:.2f})": current_price > ema13,
        f"price({current_price:.2f}) > EMA21({ema21:.2f})": current_price > ema21,
        f"price({current_price:.2f}) > VWAP({vwap:.2f})":   current_price > vwap,
    }

    failed = [k for k, v in checks.items() if not v]
    passed = len(failed) == 0
    reason = "All 4 checks passed ✅" if passed else "FAILED: " + " | ".join(failed)

    logger.info(
        "[Validator] %s — passed=%s price=%.2f ema9=%.2f ema13=%.2f ema21=%.2f vwap=%.2f — %s",
        symbol, passed, current_price, ema9, ema13, ema21, vwap, reason,
    )

    return ValidationResult(
        passed=passed,
        current_price=current_price,
        ema9=round(ema9, 4),
        ema13=round(ema13, 4),
        ema21=round(ema21, 4),
        vwap=round(vwap, 4),
        reason=reason,
    )


async def _fetch(md, symbol: str) -> tuple[list[OHLCVBar], float]:
    """Fetch bars and current price concurrently."""
    import asyncio
    bars_task  = asyncio.create_task(md.get_intraday_bars(symbol, bar_minutes=1, lookback_bars=50))
    price_task = asyncio.create_task(md.get_current_price(symbol))
    bars, price = await asyncio.gather(bars_task, price_task)
    return bars, price
