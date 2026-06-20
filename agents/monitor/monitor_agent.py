"""
monitor_agent.py

Background asyncio task that polls open paper trades every 60 seconds
and syncs their status when Alpaca closes them (TP or SL hit).

Lifecycle:
  1. Entry order pending (weekend / market closed) → leave DB as OPEN, do nothing
  2. Entry order cancelled / expired → mark DB CANCELLED
  3. Entry filled + position open on broker → keep OPEN, sync entry price
  4. Entry filled + position gone on broker → mark CLOSED (TP_HIT or SL_HIT)
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone

from config.settings import settings

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 60


async def run_monitor_agent() -> None:
    if not settings.EXECUTION_ENABLED:
        logger.info("[MonitorAgent] Disabled (EXECUTION_ENABLED=false). Not starting.")
        return

    logger.info("[MonitorAgent] ✅ Started — polling every %ds", _POLL_INTERVAL_SECONDS)

    while True:
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        try:
            await _sync_open_trades()
        except Exception as exc:
            logger.error("[MonitorAgent] Sync error: %s", exc, exc_info=True)


async def _sync_open_trades() -> None:
    from db.session import AsyncSessionLocal
    from db.models.paper_trade import PaperTrade, TradeStatus, ExitReason
    from services.v1.broker.factory import get_broker
    from services.v1.broker.order_status import classify_order_status
    from services.v1.market_data.factory import get_market_data
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PaperTrade).where(PaperTrade.status == TradeStatus.OPEN)
        )
        open_trades: list[PaperTrade] = list(result.scalars().all())

    if not open_trades:
        logger.debug("[MonitorAgent] No open trades to check.")
        return

    logger.debug("[MonitorAgent] Checking %d open trade(s).", len(open_trades))

    broker = get_broker()
    md = get_market_data()

    try:
        positions = await broker.get_open_positions()
    except Exception as exc:
        logger.error("[MonitorAgent] Could not fetch positions: %s", exc)
        return

    positions_by_symbol = {p.symbol.upper(): p for p in positions}

    async with AsyncSessionLocal() as db:
        for trade in open_trades:
            result = await db.execute(
                select(PaperTrade).where(PaperTrade.id == trade.id)
            )
            db_trade = result.scalar_one_or_none()
            if not db_trade:
                continue

            symbol = trade.symbol.upper()

            # ── Position still open on broker ─────────────────────────────
            if symbol in positions_by_symbol:
                pos = positions_by_symbol[symbol]
                if pos.avg_entry_price and abs(db_trade.entry_price - pos.avg_entry_price) > 0.01:
                    logger.info(
                        "[MonitorAgent] Synced entry price for %s: %.2f → %.2f",
                        symbol, db_trade.entry_price, pos.avg_entry_price,
                    )
                    db_trade.entry_price = pos.avg_entry_price
                continue

            # ── No broker position — check entry order before closing ───────
            if not trade.broker_order_id:
                logger.warning(
                    "[MonitorAgent] %s OPEN with no broker_order_id — skipping",
                    symbol,
                )
                continue

            try:
                order_status = await broker.get_order_status(trade.broker_order_id)
            except Exception as exc:
                logger.warning(
                    "[MonitorAgent] Could not fetch order %s for %s: %s",
                    trade.broker_order_id[:8], symbol, exc,
                )
                continue

            phase = classify_order_status(order_status)

            if phase == "pending":
                logger.debug(
                    "[MonitorAgent] %s entry order still pending (%s) — waiting for fill",
                    symbol, order_status,
                )
                continue

            if phase == "cancelled":
                db_trade.status = TradeStatus.CANCELLED
                db_trade.closed_at = datetime.now(timezone.utc)
                db_trade.validation_reason = (
                    f"{db_trade.validation_reason or ''} | "
                    f"Entry order {order_status} (never filled)"
                ).strip(" |")
                logger.info(
                    "[MonitorAgent] Order %s for %s — marked CANCELLED (status=%s)",
                    trade.broker_order_id[:8], symbol, order_status,
                )
                continue

            if phase == "unknown":
                logger.warning(
                    "[MonitorAgent] %s unknown order status %r — skipping close",
                    symbol, order_status,
                )
                continue

            # phase == "filled" — entry executed, position now closed (TP/SL)
            try:
                current_price = await md.get_current_price(trade.symbol)
            except Exception:
                current_price = None

            if current_price is not None:
                pnl_pct_raw = (current_price - db_trade.entry_price) / db_trade.entry_price
                exit_reason = (
                    ExitReason.TP_HIT if current_price >= db_trade.take_profit_price
                    else ExitReason.SL_HIT
                )
            else:
                pnl_pct_raw = None
                exit_reason = ExitReason.MANUAL

            db_trade.exit_price = current_price
            db_trade.exit_reason = exit_reason
            db_trade.pnl_pct = round(pnl_pct_raw * 100, 2) if pnl_pct_raw is not None else None
            db_trade.pnl_dollars = (
                round(pnl_pct_raw * db_trade.entry_price * trade.qty, 2)
                if pnl_pct_raw is not None else None
            )
            db_trade.status = TradeStatus.CLOSED
            db_trade.closed_at = datetime.now(timezone.utc)

            logger.info(
                "[MonitorAgent] 🔔 Trade CLOSED — %s %s | reason=%s exit=%.2f P&L=%.2f%%",
                trade.symbol, trade.id[:8],
                exit_reason.value,
                current_price or 0,
                db_trade.pnl_pct or 0,
            )

        await db.commit()
