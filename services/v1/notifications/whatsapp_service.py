"""
whatsapp_service.py

Sends WhatsApp notifications via Twilio.

Every trade event can trigger WhatsApp (currently only Discord forward is enabled):
  notify_discord_message → raw Discord text forwarded on ingest
  notify_signal_received / notify_trade_opened / notify_trade_skipped / tp / sl → reserved for later

All sends are fire-and-forget (async, non-blocking).
If Twilio fails, the error is logged and the trade pipeline continues.
"""
from __future__ import annotations
import asyncio
import logging

logger = logging.getLogger(__name__)

# Twilio sandbox prefix — required for sandbox numbers
_WA = "whatsapp:"


def _client():
    from twilio.rest import Client
    from services.v1.config.runtime_settings import runtime
    return Client(runtime.get("twilio_sid"), runtime.get("twilio_token"))


def _enabled() -> bool:
    from services.v1.config.runtime_settings import runtime
    ok = (
        runtime.get("whatsapp_enabled")
        and bool(runtime.get("twilio_sid"))
        and bool(runtime.get("twilio_token"))
        and bool(runtime.get("twilio_from"))
        and bool(runtime.get("whatsapp_to"))
    )
    return ok


async def _send(body: str) -> bool:
    """
    Send one WhatsApp message. Returns True on success.
    Always non-blocking — wrapped in try/except.
    """
    if not _enabled():
        print("[WhatsApp] Skipped — alerts disabled or Twilio not configured")
        logger.warning("[WhatsApp] Notifications disabled or not configured.")
        return False

    from services.v1.config.runtime_settings import runtime

    try:
        msg = await asyncio.to_thread(
            _client().messages.create,
            from_=f"{_WA}{runtime.get('twilio_from')}",
            to=f"{_WA}{runtime.get('whatsapp_to')}",
            body=body,
        )
        print(f"[WhatsApp] ✅ Sent — SID={msg.sid}")
        return True
    except Exception as exc:
        print(f"[WhatsApp] ❌ Failed to send: {exc}")
        logger.error("[WhatsApp] ❌ Failed to send: %s", exc)
        return False


# ── Message templates ─────────────────────────────────────────────────────────

async def notify_signal_received(
    ticker: str,
    action: str,
    entry_price: float | None,
    stop_loss: float | None,
    parse_format: str,
) -> None:
    """Sent as soon as a Discord signal is parsed successfully."""
    entry_str = f"${entry_price:.2f}" if entry_price else "market"
    sl_str    = f"${stop_loss:.2f}"   if stop_loss   else "—"

    body = (
        f"📨 Signal Received\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Ticker:  {ticker}\n"
        f"Action:  {action}\n"
        f"Entry:   {entry_str}\n"
        f"SL:      {sl_str}"
    )
    await _send(body)


async def notify_trade_opened(
    ticker: str,
    qty: int,
    entry_price: float,
    tp_price: float,
    sl_price: float,
    tp_pct: float,
    sl_pct: float,
    broker: str,
    ema9: float,
    ema13: float,
    ema21: float,
    vwap: float,
) -> None:
    """Sent when bracket order is successfully placed."""
    body = (
        f"✅ Trade Opened\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{ticker} x{qty} @ ${entry_price:.2f}\n"
        f"Broker: {broker.upper()} PAPER\n"
        f"TP: ${tp_price:.2f} (+{int(tp_pct*100)}%)\n"
        f"SL: ${sl_price:.2f} (-{int(sl_pct*100)}%)\n"
        f"EMA9  ${ema9:.2f} ✅\n"
        f"EMA13 ${ema13:.2f} ✅\n"
        f"EMA21 ${ema21:.2f} ✅\n"
        f"VWAP  ${vwap:.2f} ✅"
    )
    await _send(body)


async def notify_trade_skipped(
    ticker: str,
    current_price: float,
    reason: str,
) -> None:
    """Sent when EMA/VWAP validation fails — no trade placed."""
    # Trim reason if too long
    short_reason = reason.replace("FAILED: ", "").replace("price(", "").replace(")", "")
    if len(short_reason) > 120:
        short_reason = short_reason[:117] + "..."

    body = (
        f"❌ Signal Skipped\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Ticker: {ticker}\n"
        f"Price:  ${current_price:.2f}\n"
        f"Reason: {short_reason}\n"
        f"No trade placed."
    )
    await _send(body)


async def notify_tp_hit(
    ticker: str,
    entry_price: float,
    exit_price: float,
    pnl_pct: float,
    pnl_dollars: float,
    trade_id: str,
) -> None:
    """Sent when take profit triggers and position is closed."""
    body = (
        f"🎯 TAKE PROFIT HIT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{ticker} CLOSED ✅\n"
        f"Exit:   ${exit_price:.2f}\n"
        f"Entry:  ${entry_price:.2f}\n"
        f"P&L:    +{pnl_pct:.1f}% | +${pnl_dollars:.2f}\n"
        f"ID: {trade_id[:8]}"
    )
    await _send(body)


async def notify_sl_hit(
    ticker: str,
    entry_price: float,
    exit_price: float,
    pnl_pct: float,
    pnl_dollars: float,
    trade_id: str,
) -> None:
    """Sent when stop loss triggers and position is closed."""
    body = (
        f"🛑 STOP LOSS HIT\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{ticker} CLOSED\n"
        f"Exit:   ${exit_price:.2f}\n"
        f"Entry:  ${entry_price:.2f}\n"
        f"P&L:    {pnl_pct:.1f}% | -${abs(pnl_dollars):.2f}\n"
        f"ID: {trade_id[:8]}"
    )
    await _send(body)


async def notify_discord_message(content: str) -> bool:
    """Forward the raw Discord message text to WhatsApp."""
    text = content.strip()
    if not text:
        return False
    return await _send(text)


async def notify_test(phone_hint: str = "") -> bool:
    """Send a test message to verify the integration works."""
    body = (
        f"🤖 Trade Alert System\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"WhatsApp connected! ✅\n"
        f"You will receive alerts for:\n"
        f"• New signals from Discord\n"
        f"• Trade opened (EMA/VWAP pass)\n"
        f"• Signal skipped (EMA/VWAP fail)\n"
        f"• Take profit hit 🎯\n"
        f"• Stop loss hit 🛑\n"
        f"Broker: ALPACA PAPER\n"
        f"TP: +15% | SL: -10%"
    )
    return await _send(body)
