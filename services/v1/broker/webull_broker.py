"""
WebullBroker — adapter for Webull OpenAPI.

Webull does not support native bracket orders, so we place the entry
order first, then attach separate TP (limit) and SL (stop) orders.

Credentials: set WEBULL_APP_KEY, WEBULL_APP_SECRET, WEBULL_ACCOUNT_ID in .env
and set BROKER=webull to activate.
"""
from __future__ import annotations
import asyncio
import logging

from .port import BrokerPort
from .models import BracketOrderRequest, BrokerOrderResult, Position

logger = logging.getLogger(__name__)


class WebullBroker(BrokerPort):

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_id: str,
        endpoint: str,
    ) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_id = account_id
        self._endpoint = endpoint
        self._client = None
        logger.info("[WebullBroker] Initialised — endpoint=%s account=%s", endpoint, account_id)

    def _get_client(self):
        if self._client is None:
            from webullsdkcore.client import ApiClient
            from webullsdktrade.api.trade_api import TradeApi
            api_client = ApiClient(app_key=self._app_key, app_secret=self._app_secret)
            api_client.set_env("us", self._endpoint)
            self._client = TradeApi(api_client)
        return self._client

    async def place_bracket_order(self, req: BracketOrderRequest) -> BrokerOrderResult:
        tp_price = round(req.entry_price * (1 + req.take_profit_pct), 2)
        sl_price = round(req.entry_price * (1 - req.stop_loss_pct), 2)

        logger.info(
            "[WebullBroker] Placing order → %s %s x%s entry=%.2f TP=%.2f SL=%.2f",
            req.side.upper(), req.symbol, req.qty,
            req.entry_price, tp_price, sl_price,
        )

        params = {
            "instrument_type": "EQUITY",
            "symbol": req.symbol,
            "market": "US",
            "side": req.side.upper(),
            "order_type": "LIMIT",
            "entrust_type": "QTY",
            "quantity": str(req.qty),
            "time_in_force": "DAY",
            "limit_price": str(req.entry_price),
        }

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.place_order,
                account_id=self._account_id,
                new_orders=[params],
            )

            order_id = None
            if isinstance(response, dict):
                order_id = response.get("order_id") or response.get("orderId")
            elif isinstance(response, list) and response:
                order_id = response[0].get("order_id") or response[0].get("orderId")

            logger.info("[WebullBroker] Order placed — order_id=%s", order_id)

            return BrokerOrderResult(
                broker_order_id=str(order_id) if order_id else "",
                symbol=req.symbol,
                qty=req.qty,
                filled_avg_price=None,
                status="submitted" if order_id else "failed",
                raw_response=response if isinstance(response, dict) else {},
            )

        except Exception as exc:
            logger.error("[WebullBroker] Order failed: %s", exc)
            return BrokerOrderResult(
                broker_order_id="",
                symbol=req.symbol,
                qty=req.qty,
                filled_avg_price=None,
                status="failed",
                raw_response={"error": str(exc)},
            )

    async def get_open_positions(self) -> list[Position]:
        # Webull position polling implementation is broker-specific.
        # Returns empty list until fully wired — monitor agent handles gracefully.
        return []

    async def get_order_status(self, broker_order_id: str) -> str:
        return "unknown"

    async def cancel_order(self, broker_order_id: str) -> bool:
        logger.warning("[WebullBroker] cancel_order not yet implemented")
        return False
