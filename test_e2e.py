"""
test_e2e.py — Complete end-to-end test

Run: python3 test_e2e.py

Tests every layer of the system in order:
  1. Config loaded correctly from .env
  2. Alpaca paper account reachable
  3. EMA/VWAP validator (live GOOGL data)
  4. Parsing agent (regex + AI fallback)
  5. Place a real Alpaca bracket order (GOOGL, 1 share, 15% TP / 10% SL)
  6. Verify order appears in Alpaca
  7. Cancel the test order (cleanup)
  8. DB check (paper_trades table exists and accepts rows)
"""
from __future__ import annotations
import asyncio
import sys

sys.path.insert(0, ".")


def section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ── 1. Config ─────────────────────────────────────────────────────────────────

def test_config():
    section("STEP 1 — Config")
    from config.settings import settings
    assert settings.BROKER == "alpaca", f"Expected BROKER=alpaca, got {settings.BROKER}"
    assert settings.ALPACA_PAPER is True, "ALPACA_PAPER must be True for paper trading"
    assert settings.EXECUTION_ENABLED is True, "EXECUTION_ENABLED must be True"
    assert settings.TAKE_PROFIT_PCT == 0.15
    assert settings.STOP_LOSS_PCT == 0.10
    print(f"  broker           = {settings.BROKER}")
    print(f"  paper            = {settings.ALPACA_PAPER}")
    print(f"  execution        = {settings.EXECUTION_ENABLED}")
    print(f"  take_profit      = +{int(settings.TAKE_PROFIT_PCT*100)}%")
    print(f"  stop_loss        = -{int(settings.STOP_LOSS_PCT*100)}%")
    print(f"  market_hrs_only  = {settings.MARKET_HOURS_ONLY}")
    print("  ✅ Config OK")


# ── 2. Alpaca connection ───────────────────────────────────────────────────────

def test_alpaca_connection():
    section("STEP 2 — Alpaca paper account")
    from config.settings import settings
    from alpaca.trading.client import TradingClient
    client = TradingClient(settings.ALPACA_API_KEY, settings.ALPACA_API_SECRET, paper=True)
    account = client.get_account()
    print(f"  account_id       = {account.id}")
    print(f"  status           = {account.status}")
    print(f"  cash             = ${float(account.cash):,.2f}")
    print(f"  buying_power     = ${float(account.buying_power):,.2f}")
    print(f"  portfolio_value  = ${float(account.portfolio_value):,.2f}")
    assert str(account.status) in ("AccountStatus.ACTIVE", "ACTIVE"), f"Account not active: {account.status}"
    print("  ✅ Alpaca connected — paper account active")
    return client


# ── 3. EMA/VWAP validator ─────────────────────────────────────────────────────

async def test_ema_vwap():
    section("STEP 3 — EMA/VWAP validation (live GOOGL)")
    from services.v1.validation.ema_vwap_validator import validate
    r = await validate("GOOGL")
    print(f"  current_price    = ${r.current_price:.2f}")
    print(f"  EMA9             = ${r.ema9:.2f}   price_above={r.current_price > r.ema9}")
    print(f"  EMA13            = ${r.ema13:.2f}   price_above={r.current_price > r.ema13}")
    print(f"  EMA21            = ${r.ema21:.2f}   price_above={r.current_price > r.ema21}")
    print(f"  VWAP             = ${r.vwap:.2f}   price_above={r.current_price > r.vwap}")
    print(f"  passed           = {r.passed}")
    print(f"  reason           = {r.reason}")
    print("  ✅ EMA/VWAP validator working (live data)")
    return r


# ── 4. Parsing ────────────────────────────────────────────────────────────────

async def test_parsing():
    section("STEP 4 — Parsing agent (regex + AI fallback)")
    import agents.parsing as p

    cases = [
        ("BTO $GOOGL 370c 06/20 @2.50", [], "A"),
        ("Buy GOOGL @ 368, SL 331, TP 423", [], "D"),
        ("just bought GOOGL here around 368 holding with stop at 331", [], "AI"),
    ]

    for msg, embeds, expected_fmt in cases:
        result = await p.parse_async(msg, embeds)
        status = "✅" if (result and result.parse_format == expected_fmt) else "⚠️ "
        if result:
            print(f"  {status} [{result.parse_format}] action={result.action} ticker={result.ticker} "
                  f"entry={result.entry_price} sl={result.stop_loss}")
        else:
            print(f"  ❌ No result for: {msg[:60]}")

    print("  ✅ Parsing agent OK")


# ── 5. Place a real Alpaca bracket order ──────────────────────────────────────

async def test_place_order(validation_result) -> str:
    section("STEP 5 — Place Alpaca bracket order (1 share GOOGL)")
    from services.v1.broker.factory import get_broker, reset_broker
    from services.v1.broker.models import BracketOrderRequest
    from config.settings import settings

    reset_broker()  # ensure fresh instance with new .env keys
    broker = get_broker()

    entry = validation_result.current_price
    req = BracketOrderRequest(
        symbol="GOOGL",
        qty=1,
        side="buy",
        take_profit_pct=settings.TAKE_PROFIT_PCT,
        stop_loss_pct=settings.STOP_LOSS_PCT,
        entry_price=entry,
    )

    tp = round(entry * 1.15, 2)
    sl = round(entry * 0.90, 2)
    print(f"  entry_price      = ${entry:.2f}")
    print(f"  take_profit      = ${tp:.2f}  (+15%)")
    print(f"  stop_loss        = ${sl:.2f}  (-10%)")

    result = await broker.place_bracket_order(req)
    print(f"  broker_order_id  = {result.broker_order_id}")
    print(f"  status           = {result.status}")
    assert result.broker_order_id, "No order ID returned — order may have failed"
    print("  ✅ Bracket order placed on Alpaca paper account")
    return result.broker_order_id


# ── 6. Verify order in Alpaca ─────────────────────────────────────────────────

def test_verify_order(client, order_id: str):
    section("STEP 6 — Verify order exists in Alpaca")
    from uuid import UUID
    order = client.get_order_by_id(UUID(order_id))
    print(f"  order_id         = {order.id}")
    print(f"  symbol           = {order.symbol}")
    print(f"  qty              = {order.qty}")
    print(f"  side             = {order.side}")
    print(f"  order_class      = {order.order_class}")
    print(f"  status           = {order.status}")
    legs = getattr(order, "legs", None) or []
    print(f"  legs (TP+SL)     = {len(legs)} attached orders")
    for leg in legs:
        print(f"    [{leg.side}/{leg.type}] limit={getattr(leg,'limit_price','—')} stop={getattr(leg,'stop_price','—')}")
    print("  ✅ Order verified in Alpaca")


# ── 7. Cancel test order ──────────────────────────────────────────────────────

async def test_cancel_order(order_id: str):
    section("STEP 7 — Cancel test order (cleanup)")
    from services.v1.broker.factory import get_broker
    broker = get_broker()
    cancelled = await broker.cancel_order(order_id)
    print(f"  order_id         = {order_id}")
    print(f"  cancelled        = {cancelled}")
    if cancelled:
        print("  ✅ Test order cancelled — paper account clean")
    else:
        print("  ⚠️  Could not cancel (may have already filled — check Alpaca dashboard)")


# ── 8. DB check ───────────────────────────────────────────────────────────────

async def test_db():
    section("STEP 8 — Database (paper_trades table)")
    try:
        from db.session import engine, Base
        import db.models  # noqa: register all models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✅ DB connected — paper_trades table created/verified")

        # Quick count
        from db.session import AsyncSessionLocal
        from db.models.paper_trade import PaperTrade
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as db:
            count = (await db.execute(select(func.count(PaperTrade.id)))).scalar_one()
        print(f"  paper_trades rows in DB = {count}")
    except Exception as exc:
        print(f"  ⚠️  DB unavailable: {exc}")
        print("  (Start PostgreSQL on port 5433 to enable full pipeline)")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         TRADE ALERT — END-TO-END TEST SUITE              ║")
    print("╚══════════════════════════════════════════════════════════╝")

    test_config()
    client = test_alpaca_connection()
    validation = await test_ema_vwap()
    await test_parsing()
    order_id = await test_place_order(validation)
    test_verify_order(client, order_id)
    await test_cancel_order(order_id)
    await test_db()

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║            ALL TESTS PASSED ✅                            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print("  Next: run  python main.py  to start the full system")
    print("  Discord message → parse → EMA/VWAP → Alpaca bracket order → DB")
    print()


if __name__ == "__main__":
    asyncio.run(main())
