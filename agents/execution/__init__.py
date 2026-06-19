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
import asyncio
import logging
from datetime import datetime

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from db.models.parsed_signal import ParsedSignal, ActionType, ContractType
from db.models.paper_trade import PaperTrade, TradeStatus

logger = logging.getLogger(__name__)

# Only BUY signals trigger a new position
_ENTRY_ACTIONS = {ActionType.BUY}

# Only stock signals for now — options require different sizing
_SUPPORTED_CONTRACT_TYPES = {ContractType.STOCK, ContractType.UNKNOWN}


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
    if not settings.EXECUTION_ENABLED:
        logger.debug("[ExecutionAgent] Disabled (EXECUTION_ENABLED=false). Skipping.")
        return None

    # ── Guard: only entry actions ────────────────────────────
    if signal.action not in _ENTRY_ACTIONS:
        logger.debug("[ExecutionAgent] Action=%s — not an entry. Skipping.", signal.action)
        return None

    # ── Guard: only stocks (options sizing TBD) ──────────────
    if signal.contract_type not in _SUPPORTED_CONTRACT_TYPES:
        logger.info(
            "[ExecutionAgent] contract_type=%s not supported yet. Skipping %s.",
            signal.contract_type, signal.ticker,
        )
        return None

    # ── Guard: market hours ──────────────────────────────────
    if settings.MARKET_HOURS_ONLY and not _is_market_open():
        logger.warning("[ExecutionAgent] Market closed. Skipping %s.", signal.ticker)
        return None

    # ── Step 1: Notify signal received ───────────────────────
    from services.v1.notifications.whatsapp_service import (
        notify_signal_received, notify_trade_opened, notify_trade_skipped,
    )
    asyncio.create_task(notify_signal_received(
        ticker=signal.ticker,
        action=signal.action.value,
        entry_price=signal.entry_price,
        stop_loss=signal.stop_loss,
        parse_format=signal.parse_format,
    ))

    # ── Step 2: EMA/VWAP validation ──────────────────────────
    from services.v1.validation.ema_vwap_validator import validate
    validation = await validate(signal.ticker)

    if not validation.passed:
        logger.info(
            "[ExecutionAgent] Validation FAILED for %s — %s",
            signal.ticker, validation.reason,
        )
        await _save_skipped_trade(db, signal, validation)
        # Notify: signal skipped
        asyncio.create_task(notify_trade_skipped(
            ticker=signal.ticker,
            current_price=validation.current_price,
            reason=validation.reason,
        ))
        return None

    # ── Step 3: Place bracket order ──────────────────────────
    from services.v1.broker.factory import get_broker
    from services.v1.broker.models import BracketOrderRequest

    broker = get_broker()
    req = BracketOrderRequest(
        symbol=signal.ticker,
        qty=settings.DEFAULT_QTY,
        side="buy",
        take_profit_pct=settings.TAKE_PROFIT_PCT,
        stop_loss_pct=settings.STOP_LOSS_PCT,
        entry_price=validation.current_price,
    )

    try:
        result = await broker.place_bracket_order(req)
    except Exception as exc:
        logger.error("[ExecutionAgent] Broker error for %s: %s", signal.ticker, exc)
        return None

    # ── Step 4: Persist PaperTrade ───────────────────────────
    tp_price = round(validation.current_price * (1 + settings.TAKE_PROFIT_PCT), 2)
    sl_price = round(validation.current_price * (1 - settings.STOP_LOSS_PCT), 2)

    trade = PaperTrade(
        parsed_signal_id=signal.id,
        broker=settings.BROKER,
        broker_order_id=result.broker_order_id or None,
        symbol=signal.ticker,
        qty=settings.DEFAULT_QTY,
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
        "[ExecutionAgent] ✅ Trade opened — %s %s x%d @ %.2f | TP=%.2f SL=%.2f | order=%s",
        settings.BROKER.upper(), signal.ticker, settings.DEFAULT_QTY,
        validation.current_price, tp_price, sl_price,
        result.broker_order_id,
    )

    # ── Step 5: Notify trade opened ──────────────────────────
    asyncio.create_task(notify_trade_opened(
        ticker=signal.ticker,
        qty=settings.DEFAULT_QTY,
        entry_price=validation.current_price,
        tp_price=tp_price,
        sl_price=sl_price,
        tp_pct=settings.TAKE_PROFIT_PCT,
        sl_pct=settings.STOP_LOSS_PCT,
        broker=settings.BROKER,
        ema9=validation.ema9,
        ema13=validation.ema13,
        ema21=validation.ema21,
        vwap=validation.vwap,
    ))

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
