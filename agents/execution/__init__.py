"""
execution_agent.py

Converts a ParsedSignal into a Webull order and submits it via the
official Webull OpenAPI Python SDK.

Order lifecycle:
  ParsedSignal (BUY/SELL/EXIT) → build params → place_order() → WebullOrder row

Safety guards:
  - WEBULL_EXECUTION_ENABLED must be True (master kill-switch)
  - Market hours check (WEBULL_MARKET_HOURS_ONLY)
  - Credentials must be set
  - Actions HOLD / UPDATE are silently skipped (no order placed)
  - Duplicate guard: skip if a SUBMITTED order for same signal_id already exists
"""
from __future__ import annotations
import json
import uuid
import logging
from datetime import datetime, time, timezone

import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.settings import settings
from db.models.parsed_signal import ParsedSignal
from db.models.order import WebullOrder, OrderSide, OrderType, OrderStatus, InstrumentType

logger = logging.getLogger(__name__)

# Actions that should NEVER trigger an order
_NO_TRADE_ACTIONS = {"HOLD", "UPDATE"}

# Actions that map to a SELL side
_SELL_ACTIONS = {"SELL", "EXIT", "SL_HIT", "SCALE_OUT"}

# Eastern timezone for market hours check
_ET = pytz.timezone("America/New_York")
_MARKET_OPEN = time(9, 30)
_MARKET_CLOSE = time(16, 0)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_market_open() -> bool:
    """Return True if current ET time is within regular market hours Mon–Fri."""
    now_et = datetime.now(_ET)
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return _MARKET_OPEN <= now_et.time() < _MARKET_CLOSE


def _build_occ_symbol(ticker: str, expiry, contract_type: str, strike: float) -> str:
    """
    Build the OCC options symbol used by Webull.

    Format: TICKER(padded to 6) + YYMMDD + C/P + strike(8 digits, ×1000)
    Example: SBUX  260612C00103000
    """
    t = ticker.upper().ljust(6)
    exp = expiry.strftime("%y%m%d")
    cp = "C" if contract_type.upper() == "CALL" else "P"
    strike_int = int(round(strike * 1000))
    return f"{t}{exp}{cp}{strike_int:08d}"


def _determine_side(action: str) -> OrderSide:
    if action in _SELL_ACTIONS:
        return OrderSide.SELL
    return OrderSide.BUY


def _build_order_params(signal: ParsedSignal, client_order_id: str) -> dict:
    """Build the order params dict expected by the Webull SDK."""
    side = _determine_side(signal.action.value)
    order_type_str = settings.WEBULL_ORDER_TYPE.upper()
    qty = settings.WEBULL_DEFAULT_QTY
    is_options = signal.contract_type.value in ("CALL", "PUT")

    if is_options and signal.expiry and signal.strike:
        occ_symbol = _build_occ_symbol(
            signal.ticker, signal.expiry,
            signal.contract_type.value, signal.strike
        )
        params = {
            "instrument_type": "OPTIONS",
            "symbol": occ_symbol,
            "market": "US",
            "side": side.value,
            "order_type": order_type_str,
            "entrust_type": "QTY",
            "quantity": str(qty),
            "time_in_force": "DAY",
            "client_order_id": client_order_id,
        }
    else:
        params = {
            "instrument_type": "EQUITY",
            "symbol": signal.ticker.upper(),
            "market": "US",
            "side": side.value,
            "order_type": order_type_str,
            "entrust_type": "QTY",
            "quantity": str(qty),
            "time_in_force": "DAY",
            "support_trading_session": "N",
            "client_order_id": client_order_id,
        }

    # Attach limit price for LIMIT orders
    if order_type_str == "LIMIT" and signal.entry_price:
        params["limit_price"] = str(signal.entry_price)
    elif order_type_str == "LIMIT":
        # No entry price — fall back to MARKET to avoid rejection
        params["order_type"] = "MARKET"
        params.pop("limit_price", None)

    return params


# ── Public entry point ────────────────────────────────────────────────────────

async def execute(signal: ParsedSignal, db: AsyncSession) -> WebullOrder | None:
    """
    Attempt to place a Webull order for the given ParsedSignal.
    Returns a WebullOrder row (SUBMITTED or FAILED) or None if skipped.
    """

    # ── Guard: master kill-switch ────────────────────────────
    if not settings.WEBULL_EXECUTION_ENABLED:
        logger.debug("[ExecutionAgent] Disabled (WEBULL_EXECUTION_ENABLED=false). Skipping.")
        return None

    # ── Guard: no-trade actions ──────────────────────────────
    if signal.action.value in _NO_TRADE_ACTIONS:
        logger.info("[ExecutionAgent] Action=%s — no order placed.", signal.action.value)
        return None

    # ── Guard: market hours ──────────────────────────────────
    if settings.WEBULL_MARKET_HOURS_ONLY and not _is_market_open():
        logger.warning(
            "[ExecutionAgent] Market is closed. Skipping order for %s %s.",
            signal.action.value, signal.ticker
        )
        return None

    # ── Guard: credentials ───────────────────────────────────
    if not settings.WEBULL_APP_KEY or not settings.WEBULL_APP_SECRET or not settings.WEBULL_ACCOUNT_ID:
        logger.error(
            "[ExecutionAgent] Webull credentials not configured. "
            "Set WEBULL_APP_KEY, WEBULL_APP_SECRET, WEBULL_ACCOUNT_ID in .env"
        )
        return None

    # ── Guard: duplicate (same parsed_signal_id already submitted) ───
    existing = await db.execute(
        select(WebullOrder).where(
            WebullOrder.parsed_signal_id == signal.id,
            WebullOrder.status == OrderStatus.SUBMITTED,
        )
    )
    if existing.scalar_one_or_none():
        logger.warning("[ExecutionAgent] Duplicate order blocked for signal %s.", signal.id)
        return None

    # ── Build order params ───────────────────────────────────
    client_order_id = str(uuid.uuid4())
    params = _build_order_params(signal, client_order_id)
    side = _determine_side(signal.action.value)
    is_options = signal.contract_type.value in ("CALL", "PUT")

    # ── Create PENDING order row ─────────────────────────────
    order = WebullOrder(
        parsed_signal_id=signal.id,
        account_id=settings.WEBULL_ACCOUNT_ID,
        client_order_id=client_order_id,
        symbol=signal.ticker,
        instrument_type=InstrumentType.OPTIONS if is_options else InstrumentType.EQUITY,
        option_symbol=params.get("symbol") if is_options else None,
        strike=signal.strike,
        expiry=signal.expiry,
        contract_type=signal.contract_type.value if is_options else None,
        side=side,
        order_type=OrderType(params["order_type"]),
        quantity=settings.WEBULL_DEFAULT_QTY,
        limit_price=signal.entry_price if params["order_type"] == "LIMIT" else None,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # ── Call Webull API ──────────────────────────────────────
    try:
        from services.v1.execution.webull_client import get_trade_client
        trade_client = get_trade_client()

        logger.info(
            "[ExecutionAgent] Placing order → %s %s %s x%s %s @ %s",
            params["side"], params["instrument_type"], params["symbol"],
            params["quantity"], params["order_type"],
            params.get("limit_price", "MARKET"),
        )

        response = trade_client.place_order(
            account_id=settings.WEBULL_ACCOUNT_ID,
            new_orders=[params],
        )
        raw_resp = json.dumps(response, default=str)
        logger.info("[ExecutionAgent] Webull response: %s", raw_resp)

        # Extract Webull's order ID from response
        webull_order_id = None
        if isinstance(response, dict):
            # SDK may return nested structure — adapt as docs evolve
            webull_order_id = (
                response.get("order_id")
                or response.get("orderId")
                or response.get("data", {}).get("order_id")
            )
        elif isinstance(response, list) and response:
            webull_order_id = response[0].get("order_id") or response[0].get("orderId")

        order.webull_order_id = str(webull_order_id) if webull_order_id else None
        order.status = OrderStatus.SUBMITTED
        order.raw_response = raw_resp

    except Exception as exc:
        error_msg = str(exc)
        logger.error("[ExecutionAgent] ❌ Order failed: %s", error_msg)
        order.status = OrderStatus.FAILED
        order.error_message = error_msg

    order.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)

    status_icon = "✅" if order.status == OrderStatus.SUBMITTED else "❌"
    logger.info(
        "[ExecutionAgent] %s Order %s — status=%s webull_id=%s",
        status_icon, order.id, order.status.value, order.webull_order_id
    )
    return order
