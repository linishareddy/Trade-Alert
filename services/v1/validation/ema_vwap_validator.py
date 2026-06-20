"""
EMA/VWAP Validator

Before executing any trade, this gate checks:
  price > each configured EMA period  AND  price > VWAP

Periods, bar lookback, and bar resolution come from settings
(EMA_PERIODS, BAR_LOOKBACK, BAR_MINUTES in .env).

Returns a ValidationResult with the snapshot values stored for the DB.
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass

from config.settings import settings
from services.v1.market_data.factory import get_market_data
from services.v1.market_data.models import OHLCVBar

logger = logging.getLogger(__name__)


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


def _snapshot_emas(ema_values: dict[int, float]) -> tuple[float, float, float]:
    """Map up to three computed EMAs onto ema9/ema13/ema21 DB columns."""
    periods = settings.ema_period_list
    vals = [ema_values[p] for p in periods[:3]]
    while len(vals) < 3:
        vals.append(0.0)
    return vals[0], vals[1], vals[2]


# ── Public entry point ────────────────────────────────────────────────────────

async def validate(symbol: str) -> ValidationResult:
    """
    Fetch live bars, compute configured EMAs and VWAP, check if price is above all.
    Returns ValidationResult — caller decides whether to proceed with trade.
    """
    md = get_market_data()
    periods = settings.ema_period_list
    min_bars = settings.min_bars_required

    bars, current_price = await _fetch(md, symbol)

    if len(bars) < min_bars:
        msg = f"Only {len(bars)} bars available, need {min_bars}"
        logger.warning("[Validator] %s — %s", symbol, msg)
        return ValidationResult(
            passed=False,
            current_price=current_price,
            ema9=0.0, ema13=0.0, ema21=0.0, vwap=0.0,
            reason=msg,
        )

    closes = [b.close for b in bars]
    ema_values = {p: _ema(closes, p) for p in periods}
    vwap = _vwap(bars)
    ema9, ema13, ema21 = _snapshot_emas(ema_values)

    checks: dict[str, bool] = {
        f"price({current_price:.2f}) > EMA{p}({ema_values[p]:.2f})": current_price > ema_values[p]
        for p in periods
    }
    checks[f"price({current_price:.2f}) > VWAP({vwap:.2f})"] = current_price > vwap

    failed = [k for k, v in checks.items() if not v]
    passed = len(failed) == 0
    total_checks = len(periods) + 1
    reason = f"All {total_checks} checks passed ✅" if passed else "FAILED: " + " | ".join(failed)

    logger.info(
        "[Validator] %s — passed=%s price=%.2f periods=%s ema9=%.2f ema13=%.2f ema21=%.2f vwap=%.2f — %s",
        symbol, passed, current_price, periods, ema9, ema13, ema21, vwap, reason,
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
    bars_task = asyncio.create_task(
        md.get_intraday_bars(
            symbol,
            bar_minutes=settings.BAR_MINUTES,
            lookback_bars=settings.BAR_LOOKBACK,
        )
    )
    price_task = asyncio.create_task(md.get_current_price(symbol))
    bars, price = await asyncio.gather(bars_task, price_task)
    return bars, price
