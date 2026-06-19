"""
AlpacaBroker — adapter for Alpaca Markets paper / live trading.

Uses alpaca-py (pip install alpaca-py).
Paper account: ALPACA_PAPER=true in .env (default).

Bracket orders are natively supported by Alpaca — one API call sets
the entry, take-profit limit, and stop-loss stop in one shot.
"""
from __future__ import annotations
import asyncio
import logging
from uuid import UUID

from .port import BrokerPort
from .models import BracketOrderRequest, BrokerOrderResult, Position

logger = logging.getLogger(__name__)


class AlpacaBroker(BrokerPort):

    def __init__(self, api_key: str, api_secret: str, paper: bool = True) -> None:
        from alpaca.trading.client import TradingClient
        self._client = TradingClient(api_key, api_secret, paper=paper)
        mode = "PAPER" if paper else "LIVE"
        logger.info("[AlpacaBroker] Initialised — mode=%s", mode)

    async def place_bracket_order(self, req: BracketOrderRequest) -> BrokerOrderResult:
        from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

        tp_price = round(req.entry_price * (1 + req.take_profit_pct), 2)
        sl_price = round(req.entry_price * (1 - req.stop_loss_pct), 2)

        logger.info(
            "[AlpacaBroker] Bracket order → %s %s x%s | entry=%.2f TP=%.2f SL=%.2f",
            req.side.upper(), req.symbol, req.qty,
            req.entry_price, tp_price, sl_price,
        )

        order_req = MarketOrderRequest(
            symbol=req.symbol,
            qty=req.qty,
            side=OrderSide.BUY if req.side.lower() == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price),
        )

        order = await asyncio.to_thread(self._client.submit_order, order_req)

        return BrokerOrderResult(
            broker_order_id=str(order.id),
            symbol=str(order.symbol),
            qty=int(order.qty),
            filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            status=order.status.value,
            raw_response={"id": str(order.id), "status": order.status.value},
        )

    async def get_open_positions(self) -> list[Position]:
        positions = await asyncio.to_thread(self._client.get_all_positions)
        return [
            Position(
                symbol=str(p.symbol),
                qty=float(p.qty),
                avg_entry_price=float(p.avg_entry_price),
                current_price=float(p.current_price),
                unrealized_pnl_pct=float(p.unrealized_plpc),
                broker_order_id="",
            )
            for p in positions
        ]

    async def get_order_status(self, broker_order_id: str) -> str:
        order = await asyncio.to_thread(
            self._client.get_order_by_id, UUID(broker_order_id)
        )
        return order.status.value

    async def cancel_order(self, broker_order_id: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.cancel_order_by_id, UUID(broker_order_id)
            )
            return True
        except Exception as exc:
            logger.warning("[AlpacaBroker] Cancel failed for %s: %s", broker_order_id, exc)
            return False
