"""
execution/__init__.py

Converts a ParsedSignal into a paper trade via BrokerPort.

Pipeline:
  1. Guard checks (kill-switch, market hours, stock-only for now)
  2. EMA/VWAP validation — all 4 checks must pass
  3. Place bracket order via broker (entry + TP +15% + SL -10%)
  4. Save PaperTrade row to DB

The agent never imports Alpaca or Webull directly — it talks only to
BrokerPort. Changing BROKER= in .env swaps the broker with no code change.
"""
from __future__ import annotations
import logging
from datetime import datetime

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from services.v1.config.runtime_settings import runtime
from db.models.parsed_signal import ParsedSignal, ActionType, ContractType
from db.models.paper_trade import PaperTrade, TradeStatus

logger = logging.getLogger(__name__)

# Only BUY signals trigger a new position
_ENTRY_ACTIONS = {ActionType.BUY}


def _supported_contract_types() -> set[ContractType]:
    allowed = settings.supported_contract_names
    return {ContractType(name) for name in allowed if name in ContractType.__members__}


def _is_market_open() -> bool:
    tz = pytz.timezone(settings.MARKET_TIMEZONE)
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False
    return (
        settings.market_open_time <= now.time() < settings.market_close_time
    )


async def execute(signal: ParsedSignal, db: AsyncSession) -> PaperTrade | None:
    """
    Attempt to execute a paper trade for the parsed signal.
    Returns PaperTrade row on success, None if skipped or failed.
    """

    # ── Guard: kill-switch ───────────────────────────────────
    if not runtime.get("execution_enabled"):
        logger.debug("[ExecutionAgent] Disabled (EXECUTION_ENABLED=false). Skipping.")
        return None

    # ── Guard: only entry actions ────────────────────────────
    if signal.action not in _ENTRY_ACTIONS:
        logger.debug("[ExecutionAgent] Action=%s — not an entry. Skipping.", signal.action)
        return None

    # ── Guard: supported contract types ─────────────────────
    if signal.contract_type not in _supported_contract_types():
        logger.info(
            "[ExecutionAgent] contract_type=%s not supported yet. Skipping %s.",
            signal.contract_type, signal.ticker,
        )
        return None

    # ── Guard: market hours ──────────────────────────────────
    if runtime.get("market_hours_only") and not _is_market_open():
        logger.warning("[ExecutionAgent] Market closed. Skipping %s.", signal.ticker)
        return None

    # ── Step 1: EMA/VWAP validation ────────────────────────────
    from services.v1.validation.ema_vwap_validator import validate, ValidationResult
    from services.v1.market_data.factory import get_market_data

    if runtime.get("ema_vwap_enabled"):
        validation = await validate(signal.ticker)
        if not validation.passed:
            logger.info(
                "[ExecutionAgent] Validation FAILED for %s — %s",
                signal.ticker, validation.reason,
            )
            await _save_skipped_trade(db, signal, validation)
            return None
    else:
        # Validation bypassed — fetch live price only
        md = get_market_data()
        current_price = await md.get_current_price(signal.ticker)
        validation = ValidationResult(
            passed=True,
            current_price=current_price,
            ema9=0.0, ema13=0.0, ema21=0.0, vwap=0.0,
            reason="EMA/VWAP validation disabled (EMA_VWAP_ENABLED=false)",
        )
        logger.info("[ExecutionAgent] EMA/VWAP gate bypassed for %s @ %.2f", signal.ticker, current_price)

    # ── Step 3: Place bracket order ──────────────────────────
    from services.v1.broker.factory import get_broker
    from services.v1.broker.models import BracketOrderRequest

    tp_pct = runtime.get("take_profit_pct")
    sl_pct = runtime.get("stop_loss_pct")
    qty    = runtime.get("default_qty")

    broker = get_broker()
    req = BracketOrderRequest(
        symbol=signal.ticker,
        qty=qty,
        side="buy",
        take_profit_pct=tp_pct,
        stop_loss_pct=sl_pct,
        entry_price=validation.current_price,
    )

    try:
        result = await broker.place_bracket_order(req)
    except Exception as exc:
        logger.error("[ExecutionAgent] Broker error for %s: %s", signal.ticker, exc)
        return None

    # ── Step 4: Persist PaperTrade ───────────────────────────
    tp_price = round(validation.current_price * (1 + tp_pct), 2)
    sl_price = round(validation.current_price * (1 - sl_pct), 2)

    trade = PaperTrade(
        parsed_signal_id=signal.id,
        broker=settings.BROKER,
        broker_order_id=result.broker_order_id or None,
        symbol=signal.ticker,
        qty=qty,
        entry_price=validation.current_price,
        take_profit_price=tp_price,
        stop_loss_price=sl_price,
        status=TradeStatus.OPEN,
        validation_passed=True,
        ema9=validation.ema9,
        ema13=validation.ema13,
        ema21=validation.ema21,
        vwap=validation.vwap,
        validation_reason=validation.reason,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)

    logger.info(
        "[ExecutionAgent] ✅ Order submitted — %s %s x%d @ %.2f | TP=%.2f SL=%.2f | order=%s | broker_status=%s",
        settings.BROKER.upper(), signal.ticker, qty,
        validation.current_price, tp_price, sl_price,
        result.broker_order_id, result.status,
    )

    return trade


async def _save_skipped_trade(db: AsyncSession, signal: ParsedSignal, validation) -> None:
    """Save a CANCELLED PaperTrade so we can audit filtered signals."""
    from db.models.paper_trade import TradeStatus
    trade = PaperTrade(
        parsed_signal_id=signal.id,
        broker=settings.BROKER,
        broker_order_id=None,
        symbol=signal.ticker,
        qty=settings.DEFAULT_QTY,
        entry_price=validation.current_price,
        take_profit_price=round(validation.current_price * (1 + settings.TAKE_PROFIT_PCT), 2),
        stop_loss_price=round(validation.current_price * (1 - settings.STOP_LOSS_PCT), 2),
        status=TradeStatus.CANCELLED,
        validation_passed=False,
        ema9=validation.ema9,
        ema13=validation.ema13,
        ema21=validation.ema21,
        vwap=validation.vwap,
        validation_reason=validation.reason,
    )
    db.add(trade)
    await db.commit()
