"""
test_whatsapp.py — Live WhatsApp notification test

Run: python3 test_whatsapp.py

Sends all 5 message types to +919666501513 so you can see
exactly what each notification looks like on your phone.
"""
import asyncio, sys
sys.path.insert(0, ".")


async def main():
    from config.settings import settings
    from services.v1.notifications.whatsapp_service import (
        notify_test,
        notify_signal_received,
        notify_trade_opened,
        notify_trade_skipped,
        notify_tp_hit,
        notify_sl_hit,
    )

    print("=" * 55)
    print("  WhatsApp Notification Test")
    print(f"  Sending to: {settings.WHATSAPP_TO}")
    print(f"  From:       {settings.TWILIO_WHATSAPP_FROM}")
    print("=" * 55)

    # ── Message 1: Connection test ────────────────────────────
    print("\n[1/5] Sending connection test message...")
    ok = await notify_test()
    print(f"      {'✅ Sent' if ok else '❌ Failed'}")
    await asyncio.sleep(2)   # Twilio rate limit: 1 msg/sec

    # ── Message 2: Signal received ────────────────────────────
    print("[2/5] Sending 'signal received' notification...")
    await notify_signal_received(
        ticker="GOOGL",
        action="BUY",
        entry_price=368.03,
        stop_loss=331.23,
        parse_format="D",
    )
    print("      ✅ Sent")
    await asyncio.sleep(2)

    # ── Message 3: Trade opened ───────────────────────────────
    print("[3/5] Sending 'trade opened' notification...")
    await notify_trade_opened(
        ticker="GOOGL",
        qty=1,
        entry_price=368.03,
        tp_price=423.23,
        sl_price=331.23,
        tp_pct=0.15,
        sl_pct=0.10,
        broker="alpaca",
        ema9=367.80,
        ema13=367.50,
        ema21=367.20,
        vwap=367.90,
    )
    print("      ✅ Sent")
    await asyncio.sleep(2)

    # ── Message 4: Trade skipped ──────────────────────────────
    print("[4/5] Sending 'trade skipped' notification...")
    await notify_trade_skipped(
        ticker="TSLA",
        current_price=245.50,
        reason="FAILED: price(245.50) > EMA9(248.20) | price(245.50) > VWAP(246.80)",
    )
    print("      ✅ Sent")
    await asyncio.sleep(2)

    # ── Message 5: TP hit ─────────────────────────────────────
    print("[5/5] Sending 'take profit hit' notification...")
    await notify_tp_hit(
        ticker="GOOGL",
        entry_price=368.03,
        exit_price=423.50,
        pnl_pct=15.1,
        pnl_dollars=55.47,
        trade_id="abc12345-demo",
    )
    print("      ✅ Sent")

    print()
    print("=" * 55)
    print("  All 5 messages sent!")
    print("  Check your WhatsApp now 📱")
    print()
    print("  IMPORTANT: If you haven't joined the sandbox yet,")
    print(f"  send this from WhatsApp to {settings.TWILIO_WHATSAPP_FROM}:")
    print("  > Go to Twilio Console → Messaging → Try it out")
    print("    → Send a WhatsApp message → copy the join code")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
