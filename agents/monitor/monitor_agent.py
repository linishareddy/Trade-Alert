"""
monitor_agent.py

Background asyncio task that polls open paper trades every 60 seconds
and syncs their status when Alpaca closes them (TP or SL hit).

Why this works with Alpaca bracket orders:
  When you place a bracket order, Alpaca creates THREE linked orders:
    - Entry (market)
    - Take-profit (limit at +15%)
    - Stop-loss (stop at -10%)
  When either the TP or SL fills, Alpaca cancels the other and the
  position disappears from get_all_positions(). We detect this and
  mark the trade CLOSED with the correct exit reason.
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

    # Fetch live broker positions
    try:
        positions = await broker.get_open_positions()
    except Exception as exc:
        logger.error("[MonitorAgent] Could not fetch positions: %s", exc)
        return

    open_symbols = {p.symbol.upper() for p in positions}

    async with AsyncSessionLocal() as db:
        for trade in open_trades:
            if trade.symbol.upper() in open_symbols:
                continue  # still open, nothing to do

            # Position is gone → TP or SL was hit
            try:
                current_price = await md.get_current_price(trade.symbol)
            except Exception:
                current_price = None

            if current_price is not None:
                pnl_pct_raw = (current_price - trade.entry_price) / trade.entry_price
                exit_reason = (
                    ExitReason.TP_HIT if current_price >= trade.take_profit_price
                    else ExitReason.SL_HIT
                )
            else:
                pnl_pct_raw = None
                exit_reason = ExitReason.MANUAL

            # Re-fetch the trade in this session for update
            result = await db.execute(
                select(PaperTrade).where(PaperTrade.id == trade.id)
            )
            db_trade = result.scalar_one_or_none()
            if not db_trade:
                continue

            db_trade.exit_price = current_price
            db_trade.exit_reason = exit_reason
            db_trade.pnl_pct = round(pnl_pct_raw * 100, 2) if pnl_pct_raw is not None else None
            db_trade.pnl_dollars = (
                round(pnl_pct_raw * trade.entry_price * trade.qty, 2)
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
