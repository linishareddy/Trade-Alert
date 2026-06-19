# Trade Alert System — Complete Architecture & Code Reference

> **Last updated:** June 2026  
> **Stack:** Python 3.11 · FastAPI · PostgreSQL · Alpaca Paper Trading · Twilio WhatsApp · Groq AI

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Complete File Structure](#2-complete-file-structure)
3. [Architecture Pattern — Ports & Adapters](#3-architecture-pattern--ports--adapters)
4. [Full Data Flow — Discord to WhatsApp](#4-full-data-flow--discord-to-whatsapp)
5. [Agent 1 — Discord Ingestion Agent](#5-agent-1--discord-ingestion-agent)
6. [Agent 2 — Parsing Agent (Regex + AI)](#6-agent-2--parsing-agent-regex--ai)
7. [Agent 3 — EMA/VWAP Validation](#7-agent-3--emavwap-validation)
8. [Agent 4 — Execution Agent](#8-agent-4--execution-agent)
9. [Agent 5 — Position Monitor Agent](#9-agent-5--position-monitor-agent)
10. [Broker Layer — Ports & Adapters](#10-broker-layer--ports--adapters)
11. [Market Data Layer](#11-market-data-layer)
12. [WhatsApp Notification Service](#12-whatsapp-notification-service)
13. [Database Schema](#13-database-schema)
14. [API Endpoints](#14-api-endpoints)
15. [All Rules & Guard Checks](#15-all-rules--guard-checks)
16. [Environment Configuration (.env)](#16-environment-configuration-env)
17. [How to Swap Brokers](#17-how-to-swap-brokers)
18. [How to Add a New Broker](#18-how-to-add-a-new-broker)
19. [Error Handling Strategy](#19-error-handling-strategy)
20. [Running the System](#20-running-the-system)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DISCORD CHANNEL                               │
│   "BTO $GOOGL 370c 06/20 @2.50"  or  "Buy GOOGL @ 368, SL 331"    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ WebSocket (self-bot)
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                  Agent 1: Discord Ingestion Agent                  │
│               agents/discord/discord_agent.py                      │
│  • Watches specific channel IDs as your personal account           │
│  • Human-like delay (0.8–2.3s) before forwarding                  │
│  • POST /api/v1/ingest/alert  →  FastAPI server                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │ HTTP POST (localhost)
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                       │
│   router → controller → ingestion_service (pipeline)              │
│                                                                    │
│   Step 1: Deduplicate (skip already-seen message IDs)             │
│   Step 2: Save raw alert to DB (raw_alerts table)                 │
│   Step 3: Agent 2 — Parse (regex → AI fallback)                   │
│   Step 4: Match follow-ups to parent signals                       │
│   Step 5: Save ParsedSignal to DB (parsed_signals table)          │
│   Step 6: Agent 4 — Execute trade pipeline                        │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│               Agent 4: Execution Agent                             │
│               agents/execution/__init__.py                         │
│                                                                    │
│   Guard 1:  EXECUTION_ENABLED = true?                             │
│   Guard 2:  Action is BUY?                                        │
│   Guard 3:  Instrument is STOCK?                                  │
│   Guard 4:  Market hours 9:30–16:00 ET? (if MARKET_HOURS_ONLY)   │
│                                                                    │
│   ── WhatsApp #1: "Signal received, checking EMA/VWAP..."         │
│                                                                    │
│   Agent 3:  EMA/VWAP Validation                                   │
│     price > EMA9 AND EMA13 AND EMA21 AND VWAP?                    │
│     FAIL → WhatsApp #2: "Signal skipped"  → stop                 │
│     PASS → continue                                               │
│                                                                    │
│   Broker Factory → AlpacaBroker                                   │
│     place_bracket_order(entry, TP +15%, SL -10%)                  │
│     ONE API call → 3 linked orders on Alpaca paper                │
│                                                                    │
│   Save PaperTrade to DB                                           │
│   ── WhatsApp #2: "Trade opened GOOGL @ $368"                     │
└───────────────────────────┬───────────────────────────────────────┘
                            │ (Alpaca monitors position automatically)
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│               Agent 5: Position Monitor Agent                      │
│               agents/monitor/monitor_agent.py                      │
│                                                                    │
│   Runs every 60 seconds (background asyncio loop)                 │
│   broker.get_open_positions() → compare with open paper_trades    │
│   Position gone? → TP or SL was hit by Alpaca                    │
│   Update paper_trade: status=CLOSED, exit_price, pnl_pct          │
│   ── WhatsApp #3: "🎯 TP HIT GOOGL +15.1% +$55.47"              │
│                or  "🛑 SL HIT GOOGL -10.0% -$36.80"              │
└───────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete File Structure

```
Trade-Alert/
│
├── main.py                            Entry point — starts 3 async tasks
├── requirements.txt                   All Python dependencies
├── .env                               Credentials & config (never commit)
├── .env.example                       Template for .env
├── test_e2e.py                        End-to-end test (Alpaca + EMA/VWAP)
├── test_whatsapp.py                   WhatsApp notification test
│
├── config/
│   └── settings.py                    Pydantic settings — reads from .env
│
├── agents/                            The 5 autonomous agents
│   ├── discord/
│   │   ├── discord_agent.py           Agent 1 — self-bot watching Discord
│   │   └── harness/
│   │       └── client.py              HTTP client to POST alerts to FastAPI
│   ├── parsing/
│   │   └── __init__.py                Agent 2 — regex parser + Groq AI fallback
│   ├── execution/
│   │   └── __init__.py                Agent 4 — runs guards, EMA/VWAP, executes
│   └── monitor/
│       └── monitor_agent.py           Agent 5 — polls positions every 60s
│
├── services/
│   └── v1/
│       ├── broker/                    BROKER PORT LAYER
│       │   ├── port.py                Abstract interface (BrokerPort)
│       │   ├── models.py              Broker-agnostic data models
│       │   ├── factory.py             get_broker() → right adapter from .env
│       │   ├── alpaca_broker.py       AlpacaBroker (implements BrokerPort)
│       │   └── webull_broker.py       WebullBroker (implements BrokerPort)
│       │
│       ├── market_data/               MARKET DATA PORT LAYER
│       │   ├── port.py                Abstract interface (MarketDataPort)
│       │   ├── models.py              OHLCVBar dataclass
│       │   ├── factory.py             get_market_data() → right adapter
│       │   ├── yfinance_adapter.py    YFinanceData (free, 15min delay)
│       │   └── alpaca_data_adapter.py AlpacaData (real-time)
│       │
│       ├── validation/                SIGNAL VALIDATION
│       │   └── ema_vwap_validator.py  EMA9/13/21 + VWAP math
│       │
│       ├── notifications/             WHATSAPP NOTIFICATIONS
│       │   └── whatsapp_service.py    Twilio client + 5 message templates
│       │
│       ├── discord/
│       │   └── ingestion_service.py   6-step ingest pipeline
│       │
│       ├── signals/
│       │   └── signal_service.py      DB CRUD for ParsedSignal
│       │
│       └── trades/
│           └── trade_service.py       DB CRUD for PaperTrade + summary stats
│
├── controllers/
│   └── v1/
│       ├── ingest/
│       │   └── ingest_controller.py   Translate ingest schema ↔ service
│       ├── signals/
│       │   └── signal_controller.py   Signal list/get logic
│       └── trades/
│           └── trade_controller.py    Trade list/get/summary logic
│
├── routers/
│   └── v1/
│       ├── health.py                  GET /health
│       ├── ingest.py                  POST /ingest/alert
│       ├── signals.py                 GET /signals
│       └── trades.py                  GET /trades, /trades/summary, /trades/{id}
│
├── schemas/
│   └── v1/
│       ├── ingest.py                  RawAlertIn, IngestResponse
│       ├── signals.py                 Signal response schemas
│       ├── health.py                  Health response schema
│       └── trades.py                  PaperTradeResponse, TradeSummaryResponse
│
├── db/
│   ├── session.py                     SQLAlchemy async engine + session factory
│   └── models/
│       ├── __init__.py                Imports all models (for create_all)
│       ├── raw_alert.py               Table: raw_alerts
│       ├── parsed_signal.py           Table: parsed_signals
│       ├── paper_trade.py             Table: paper_trades
│       └── order.py                   Table: webull_orders (legacy)
│
└── models/
    └── v1/
        └── parsing/
            └── parsed_signal_dto.py   Internal DTO between parser and service
```

---

## 3. Architecture Pattern — Ports & Adapters

The system uses **Hexagonal Architecture** (Ports & Adapters). Business logic never knows which broker or data provider is active. It talks only to abstract interfaces (Ports). The right implementation (Adapter) is injected at runtime via factory + `.env` config.

```
┌──────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC                        │
│              (agents/execution, agents/monitor)           │
│                                                          │
│   broker = get_broker()          ← only this import     │
│   md     = get_market_data()     ← only this import     │
└──────────┬───────────────────────────────┬───────────────┘
           │                               │
           ▼                               ▼
    ┌─────────────┐                 ┌─────────────────┐
    │  BrokerPort │                 │ MarketDataPort  │
    │ (abstract)  │                 │  (abstract)     │
    └──────┬──────┘                 └────────┬────────┘
           │                                 │
     ┌─────┴──────┐                   ┌──────┴───────┐
     │            │                   │              │
AlpacaBroker  WebullBroker      YFinanceData   AlpacaData
```

**To swap brokers:** Change one line in `.env`:
```
BROKER=alpaca   →   BROKER=webull
```
Zero code changes required.

**To swap market data:** Change one line in `.env`:
```
MARKET_DATA_PROVIDER=yfinance   →   MARKET_DATA_PROVIDER=alpaca
```

---

## 4. Full Data Flow — Discord to WhatsApp

```
TIME →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→

T+0s   Discord message arrives in channel
       "Buy GOOGL @ 368, SL 331"

T+1s   Discord Agent (self-bot) receives via WebSocket
       Sleeps 0.8–2.3s (human-like delay)
       POST /api/v1/ingest/alert
         {message_id, channel_id, author, content, embeds}

T+1s   FastAPI: router → controller → ingestion_service

T+1s   STEP 1: Deduplicate
         SELECT raw_alerts WHERE message_id = X
         → Not found, continue

T+1s   STEP 2: Save raw alert
         INSERT INTO raw_alerts
         → Saved (always, even if not a trading signal)

T+1s   STEP 3: Parse
         Try Format A (BTO/STC regex)     → no match
         Try Format B (index block regex) → no match
         Try Format C (Discord embed)     → no match
         Try Format D (plain text regex)  → MATCH ✅
         → ParsedSignalDTO {action=BUY, ticker=GOOGL, entry=368, sl=331}

T+1s   STEP 4: Match follow-ups
         action=BUY → not a follow-up, skip

T+1s   STEP 5: Save ParsedSignal
         INSERT INTO parsed_signals
         → {ticker=GOOGL, action=BUY, entry_price=368, stop_loss=331}

T+1s   STEP 6: Execute → agents/execution

T+1s   Guard 1: EXECUTION_ENABLED=true ✅
       Guard 2: action=BUY ✅
       Guard 3: contract_type=STOCK ✅
       Guard 4: market hours (or MARKET_HOURS_ONLY=false) ✅

T+2s   📱 WhatsApp #1:
         "📨 New Signal Detected
          Ticker: GOOGL | Action: BUY
          Entry: $368.00 | SL: $331.00
          Checking EMA/VWAP..."

T+2s   Fetch 50 bars of 1-min data (yfinance) + current price
       Compute EMA9, EMA13, EMA21, VWAP

T+3s   VALIDATION CHECK:
         price($368.03) > EMA9($367.80)  ✅
         price($368.03) > EMA13($367.50) ✅
         price($368.03) > EMA21($367.20) ✅
         price($368.03) > VWAP($367.90)  ✅
         ALL PASS → continue to execution

T+3s   AlpacaBroker.place_bracket_order()
         Alpaca API call → 3 linked orders:
           Market BUY GOOGL 1 share
           Limit SELL @ $423.23 (+15% TP)
           Stop  SELL @ $331.23 (-10% SL)

T+3s   INSERT INTO paper_trades
         {entry=368.03, tp=423.23, sl=331.23,
          ema9=367.80, ema13=367.50, ema21=367.20, vwap=367.90,
          status=OPEN, broker_order_id=UUID}

T+4s   📱 WhatsApp #2:
         "✅ Trade Opened
          GOOGL x1 @ $368.03
          TP: $423.23 (+15%)
          SL: $331.23 (-10%)
          EMA9✅ EMA13✅ EMA21✅ VWAP✅"

         ... time passes, Alpaca fills entry, holds position ...

T+60s  Monitor Agent polls:
         broker.get_open_positions() → GOOGL still there
         No action.

         ... more time passes, GOOGL rises to $423.50 ...

         Alpaca auto-fills SELL LIMIT @ $423.23 (TP hit)
         Alpaca auto-cancels SELL STOP (other leg)
         Position disappears from Alpaca

T+N min Monitor Agent polls:
         broker.get_open_positions() → GOOGL NOT there
         current_price = $423.50
         pnl_pct = (423.50 - 368.03) / 368.03 = +15.1%
         price >= tp_price → exit_reason = TP_HIT
         UPDATE paper_trades SET status=CLOSED, pnl_pct=15.1, exit_price=423.50

T+N min 📱 WhatsApp #3:
         "🎯 TAKE PROFIT HIT
          GOOGL CLOSED ✅
          Exit: $423.50 | Entry: $368.03
          P&L: +15.1% | +$55.47"
```

---

## 5. Agent 1 — Discord Ingestion Agent

**File:** `agents/discord/discord_agent.py`

### What it does
Runs as a Discord **self-bot** — it logs into Discord using YOUR personal user token (not a bot token). This means it can read channels that bots are not invited to.

### Key classes

**`TradingBot(discord.Client)`**
- `on_ready()` — subscribes to target channels using Discord's Lazy Request (opcode 14). This is required for self-bots to receive live `MESSAGE_CREATE` events.
- `on_message()` — fires on every new message. Filters to target channel IDs only. Ignores messages from your own account.
- `on_message_edit()` — fires when a message is edited. Re-processes with `is_edit=True`.
- `_process()` — sleeps 0.8–2.3 seconds (random, looks human), then POSTs to ingest endpoint.

### Channel subscription (important detail)
Standard Discord bots receive events for all guilds they join. Self-bots do NOT automatically receive message events. The Lazy Request (opcode 14) explicitly tells Discord's gateway "subscribe me to events in this channel". Without it, no messages arrive.

```python
payload = {
    "op": 14,
    "d": {
        "guild_id": str(channel.guild.id),
        "channels": {str(channel.id): [[0, 99]]}
    }
}
await self.ws.send_as_json(payload)
```

### POST payload structure
```json
{
  "message_id": "1234567890",
  "channel_id": "9876543210",
  "author": "TraderJoe#1234",
  "content": "Buy GOOGL @ 368, SL 331",
  "embeds": [],
  "timestamp": "2026-06-19T10:00:00Z",
  "is_edit": false
}
```

### Harness client: `agents/discord/harness/client.py`
Simple `httpx.AsyncClient` that POSTs to `INGEST_URL` (default: `http://127.0.0.1:8000/api/v1/ingest/alert`). Returns `True` on HTTP 200, `False` on any error. The agent continues even if the server is temporarily down.

---

## 6. Agent 2 — Parsing Agent (Regex + AI)

**File:** `agents/parsing/__init__.py`

### Priority order
```
Format A → Format B → Format C → Format D → Groq AI
```
Each format is tried in order. First match wins. AI only activates if ALL regex formats fail.

### Format A — Shorthand options
Pattern: `BTO/STC $TICKER STRIKEc/p MM/DD @PRICE`
```
BTO $SBUX 103c 06/12 @0.55
STC $AAPL 180p 12/15/26 @2.10
```
Extracts: action, ticker, strike, contract_type (CALL/PUT), expiry, entry_price

### Format B — Index/spread block (2 lines)
Pattern: ticker + CALL/PUT + price on line 1, then YYMMDD + strike + SL on line 2
```
SPXW PUT 8.70
260610 7275.00 8.50
```
Extracts: ticker, contract_type, expiry (YYMMDD format), strike, entry_price, stop_loss

### Format C — Discord embed
Triggered when message has Discord embeds with `title` = known action word.
Fields parsed: `contract` (e.g., "QQQ $742c"), `price` (e.g., "$2.05")

### Format D — Plain text (catch-all)
```
Buy TSLA @ 250, TP 270, SL 245
Sell $AAPL @ 180 SL 185 TP 170
Long $NVDA @ 120
```
Uses separate regex for: action keyword, `$TICKER`, `@ price`, `TP/TARGET price`, `SL/STOP price`

**Noise words filtered:** BTO, STC, BUY, SELL, TP, SL, AT, OR, THE, AND, FOR, STOP, LOSS... (prevents "STOP" being treated as a ticker)

### AI Fallback — Groq Llama 3.3
Activates when: all 4 formats fail AND `AI_PARSING_ENABLED=true` AND `GROQ_API_KEY` set.

```python
# Model used:
"llama-3.3-70b-versatile"

# Prompt instructs it to return exact JSON:
{
  "action": "BUY|SELL|EXIT|...",
  "ticker": "GOOGL",
  "contract_type": "STOCK|CALL|PUT|UNKNOWN",
  "entry_price": 368.00,
  "stop_loss": 331.00,
  "target_price": null
}
```

If AI returns `{"action": null}` → message is not a trading signal.

### Entry point
- `parse(content, embeds)` — synchronous, regex only
- `parse_async(content, embeds)` — async, regex first then AI fallback

**Used by:** `ingestion_service.py` calls `await parsing_agent.parse_async(...)`

---

## 7. Agent 3 — EMA/VWAP Validation

**File:** `services/v1/validation/ema_vwap_validator.py`

### The 4 checks (ALL must pass)
```
price > EMA9   (9-period exponential moving average)
price > EMA13  (13-period exponential moving average)
price > EMA21  (21-period exponential moving average)
price > VWAP   (volume-weighted average price, intraday)
```

This mirrors the chart pattern from the signal: price must be above the three short EMAs and above the VWAP line. If price dips below ANY of these, the market structure is weakening — we skip.

### EMA formula
```python
def _ema(closes: list[float], period: int) -> float:
    k = 2.0 / (period + 1)           # smoothing factor
    ema = sum(closes[:period]) / period  # seed: simple average of first N bars
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)  # exponential weighting
    return ema
```

### VWAP formula
```python
def _vwap(bars: list[OHLCVBar]) -> float:
    # Typical price = (high + low + close) / 3
    # VWAP = Σ(typical_price × volume) / Σ(volume)
    cum_tp_vol = sum((b.high + b.low + b.close) / 3 * b.volume for b in bars)
    cum_vol    = sum(b.volume for b in bars)
    return cum_tp_vol / cum_vol
```

### Data requirements
- Minimum 21 bars (to compute EMA21)
- Default: fetch 50 bars of 1-minute resolution
- `lookback_bars=50` means the last 50 minutes of intraday trading

### Return value: `ValidationResult`
```python
@dataclass
class ValidationResult:
    passed: bool           # True only if ALL 4 checks pass
    current_price: float   # Live price at time of check
    ema9: float
    ema13: float
    ema21: float
    vwap: float
    reason: str            # Human-readable explanation (also stored in DB)
```

### Concurrent fetching
Bars and current price are fetched at the same time using `asyncio.gather()`:
```python
bars, price = await asyncio.gather(
    md.get_intraday_bars(symbol, bar_minutes=1, lookback_bars=50),
    md.get_current_price(symbol),
)
```

---

## 8. Agent 4 — Execution Agent

**File:** `agents/execution/__init__.py`

### Guard chain (all must pass before any API call is made)

```
Guard 1: EXECUTION_ENABLED = true
         → if false: log debug, return None silently
         → Reason: master kill-switch, prevents accidental real trades

Guard 2: signal.action in {BUY}
         → if EXIT/SELL/HOLD/UPDATE/etc: return None
         → Reason: only entry signals open new positions

Guard 3: signal.contract_type in {STOCK, UNKNOWN}
         → if CALL/PUT: log info, return None
         → Reason: options require different position sizing logic
         → Future: add options support with contract multiplier

Guard 4: market hours check (only if MARKET_HOURS_ONLY=true)
         → checks ET timezone, Mon–Fri, 9:30–16:00
         → if closed: log warning, return None
         → MARKET_HOURS_ONLY=false bypasses this (used in testing)
```

### Execution steps (after all guards pass)

```
Step 1: Notify WhatsApp — "Signal received, checking EMA/VWAP"
        (fire-and-forget asyncio task, doesn't block execution)

Step 2: EMA/VWAP validation
        → FAIL: save CANCELLED paper_trade, notify WhatsApp, return None
        → PASS: continue

Step 3: Build BracketOrderRequest (broker-agnostic)
        symbol=GOOGL, qty=1, side="buy",
        take_profit_pct=0.15, stop_loss_pct=0.10,
        entry_price=validation.current_price (live price, NOT signal price)

Step 4: broker.place_bracket_order(request)
        → AlpacaBroker translates to Alpaca API
        → Returns BrokerOrderResult {broker_order_id, status, filled_price}
        → On exception: log error, return None (no DB write, no notification)

Step 5: INSERT paper_trade with full validation snapshot
        → status=OPEN, validation_passed=True
        → EMA/VWAP values frozen at time of trade (for audit)

Step 6: Notify WhatsApp — "Trade opened" with all details
        (fire-and-forget)
```

### Why live price, not signal price?
The signal may say "entry $368" but by the time the message arrives, gets parsed, validated, and executed, the price may have moved. We use `validation.current_price` (fetched from yfinance during the EMA/VWAP check) as the actual entry reference. Alpaca places a market order which fills at the best available price.

### Skipped trade record
Even when validation fails, a `CANCELLED` paper_trade row is saved with `validation_passed=False`. This lets you audit: "how many signals came in, how many were filtered by EMA/VWAP, how many actually traded."

---

## 9. Agent 5 — Position Monitor Agent

**File:** `agents/monitor/monitor_agent.py`

### What it does
Runs as a forever loop, waking every 60 seconds. Compares open paper trades in the DB against live positions from the broker. When a position disappears (Alpaca closed it via TP or SL), it records the result and sends a WhatsApp notification.

### Why this works with Alpaca bracket orders
When you place a bracket order, Alpaca creates 3 linked orders:
1. **Entry** (market) — fills immediately, you now hold the position
2. **Take-profit** (limit sell at +15%) — waits
3. **Stop-loss** (stop sell at -10%) — waits

When **either** the TP or SL fills:
- Alpaca auto-fills one leg
- Alpaca auto-cancels the other leg
- Position disappears from `get_all_positions()`

The monitor detects the disappearance and determines exit reason by comparing current price to TP/SL levels.

### Exit reason logic
```python
if current_price >= trade.take_profit_price:
    exit_reason = ExitReason.TP_HIT
else:
    exit_reason = ExitReason.SL_HIT
```

### P&L calculation
```python
pnl_pct_raw = (exit_price - entry_price) / entry_price
pnl_pct     = round(pnl_pct_raw * 100, 2)     # e.g. 15.1
pnl_dollars = round(pnl_pct_raw * entry_price * qty, 2)  # e.g. 55.47
```

### Starts only if `EXECUTION_ENABLED=true`
If execution is disabled, the monitor exits immediately. No point polling Alpaca if no trades are being placed.

---

## 10. Broker Layer — Ports & Adapters

### BrokerPort (abstract interface)
**File:** `services/v1/broker/port.py`

```python
class BrokerPort(ABC):
    async def place_bracket_order(self, request: BracketOrderRequest) -> BrokerOrderResult
    async def get_open_positions(self) -> list[Position]
    async def get_order_status(self, broker_order_id: str) -> str
    async def cancel_order(self, broker_order_id: str) -> bool
```

### Broker-agnostic models
**File:** `services/v1/broker/models.py`

```python
@dataclass
class BracketOrderRequest:
    symbol: str
    qty: int
    side: str             # "buy" | "sell"
    take_profit_pct: float  # 0.15 for 15%
    stop_loss_pct: float    # 0.10 for 10%
    entry_price: float

@dataclass
class BrokerOrderResult:
    broker_order_id: str
    symbol: str
    qty: int
    filled_avg_price: float | None
    status: str           # "submitted" | "filled" | "failed"
    raw_response: dict

@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl_pct: float
    broker_order_id: str
```

### AlpacaBroker
**File:** `services/v1/broker/alpaca_broker.py`

- Uses `alpaca-py` SDK (`TradingClient`)
- All Alpaca calls wrapped in `asyncio.to_thread()` (SDK is sync, we run it in a thread pool)
- Bracket orders: `OrderClass.BRACKET` with `TakeProfitRequest` + `StopLossRequest`
- Paper mode: `TradingClient(key, secret, paper=True)`

### WebullBroker
**File:** `services/v1/broker/webull_broker.py`

- Uses `webull-openapi-python-sdk`
- Webull does NOT support native bracket orders — entry is placed as a limit order
- TP/SL must be managed manually (partially implemented, or use BROKER=alpaca)
- Activate: set `BROKER=webull` in `.env` + provide Webull credentials

### Factory
**File:** `services/v1/broker/factory.py`

```python
def get_broker() -> BrokerPort:
    match settings.BROKER.lower():
        case "alpaca": return AlpacaBroker(...)
        case "webull": return WebullBroker(...)
        case other:    raise ValueError(f"Unknown broker '{other}'")
```

Singleton pattern — same instance reused across all requests in a process.

---

## 11. Market Data Layer

### MarketDataPort (abstract interface)
**File:** `services/v1/market_data/port.py`

```python
class MarketDataPort(ABC):
    async def get_current_price(self, symbol: str) -> float
    async def get_intraday_bars(self, symbol: str, bar_minutes: int, lookback_bars: int) -> list[OHLCVBar]
```

### YFinanceData (default)
**File:** `services/v1/market_data/yfinance_adapter.py`

- Free, no API key needed
- Uses `yfinance.Ticker.history(period="1d", interval="1m")`
- Price from `ticker.fast_info.last_price`
- May have 15-minute delay for some symbols
- Good for paper trading / testing

### AlpacaData (real-time option)
**File:** `services/v1/market_data/alpaca_data_adapter.py`

- Real-time market data via Alpaca free plan
- Uses same API key as broker
- `StockHistoricalDataClient` for bars, `StockLatestTradeRequest` for price
- Activate: set `MARKET_DATA_PROVIDER=alpaca` in `.env`

### OHLCVBar
```python
@dataclass
class OHLCVBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
```

---

## 12. WhatsApp Notification Service

**File:** `services/v1/notifications/whatsapp_service.py`

### Twilio integration
- SDK: `twilio` Python library
- Sends via Twilio WhatsApp Sandbox: `from_='whatsapp:+14155238886'`
- Recipient: `to='whatsapp:+919666501513'`
- All sends wrapped in `asyncio.to_thread()` (Twilio SDK is sync)
- All sends wrapped in `try/except` — notification failure NEVER stops a trade

### 5 message templates

| Function | Triggered by | When |
|---|---|---|
| `notify_signal_received()` | Execution Agent | Signal parsed, before EMA/VWAP check |
| `notify_trade_opened()` | Execution Agent | Bracket order placed on Alpaca |
| `notify_trade_skipped()` | Execution Agent | EMA/VWAP validation failed |
| `notify_tp_hit()` | Monitor Agent | Take profit hit, position closed |
| `notify_sl_hit()` | Monitor Agent | Stop loss hit, position closed |

### Fire-and-forget pattern
Notifications use `asyncio.create_task()` — they run concurrently with the main pipeline and do not block it:
```python
asyncio.create_task(notify_trade_opened(...))
# execution continues immediately, notification delivers in background
```

### Guard: `_enabled()`
Before every send, checks all 4 of:
1. `WHATSAPP_NOTIFICATIONS_ENABLED=true`
2. `TWILIO_ACCOUNT_SID` not empty
3. `TWILIO_AUTH_TOKEN` not empty
4. `TWILIO_WHATSAPP_FROM` not empty
5. `WHATSAPP_TO` not empty

If any missing → logs debug, returns False, no exception raised.

### Sandbox note
Twilio WhatsApp Sandbox requires the recipient to send a one-time join message.
After 72 hours of inactivity, re-send the join code.

---

## 13. Database Schema

### Table: `raw_alerts`
Every Discord message that arrives — even non-signal messages. Full audit log.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `message_id` | VARCHAR(32) UNIQUE | Discord message snowflake ID (deduplication key) |
| `channel_id` | VARCHAR(32) | Discord channel ID |
| `author` | VARCHAR(128) | Discord username#discriminator |
| `content` | TEXT | Raw message text |
| `embeds` | JSON | Discord embed objects |
| `is_edit` | BOOLEAN | True if this was a message edit |
| `received_at` | TIMESTAMPTZ | When we received it |

### Table: `parsed_signals`
Structured trading intent extracted from raw alerts.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `raw_alert_id` | UUID FK | Links to raw_alerts |
| `parent_id` | UUID FK (self) | Follow-up signals link to their parent |
| `action` | ENUM | BUY, SELL, EXIT, SL_HIT, SCALE_IN, SCALE_OUT, HOLD, UPDATE |
| `status` | ENUM | OPEN, PARTIAL, CLOSED |
| `ticker` | VARCHAR(16) | e.g. GOOGL |
| `contract_type` | ENUM | STOCK, CALL, PUT, UNKNOWN |
| `strike` | FLOAT | Options strike price |
| `expiry` | DATE | Options expiry date |
| `entry_price` | FLOAT | Price from signal (may differ from actual fill) |
| `target_price` | FLOAT | Take-profit from signal |
| `stop_loss` | FLOAT | Stop-loss from signal |
| `parse_format` | VARCHAR(16) | A, B, C, D, or AI |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### Table: `paper_trades`
One row per executed bracket order. Tracks full lifecycle.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `parsed_signal_id` | UUID FK | Links to parsed_signals |
| `broker` | VARCHAR(32) | "alpaca" or "webull" |
| `broker_order_id` | VARCHAR(128) | Alpaca order UUID |
| `symbol` | VARCHAR(16) | e.g. GOOGL |
| `qty` | INTEGER | Number of shares |
| `entry_price` | FLOAT | Live price at time of execution |
| `take_profit_price` | FLOAT | entry × 1.15 |
| `stop_loss_price` | FLOAT | entry × 0.90 |
| `exit_price` | FLOAT | Filled when trade closes |
| `exit_reason` | ENUM | TP_HIT, SL_HIT, MANUAL |
| `pnl_pct` | FLOAT | e.g. 15.1 for +15.1% |
| `pnl_dollars` | FLOAT | e.g. 55.47 |
| `status` | ENUM | OPEN, CLOSED, CANCELLED |
| `validation_passed` | BOOLEAN | True = EMA/VWAP passed, False = CANCELLED |
| `ema9` | FLOAT | EMA9 snapshot at trade time |
| `ema13` | FLOAT | EMA13 snapshot at trade time |
| `ema21` | FLOAT | EMA21 snapshot at trade time |
| `vwap` | FLOAT | VWAP snapshot at trade time |
| `validation_reason` | TEXT | Full reason string |
| `created_at` | TIMESTAMPTZ | When trade opened |
| `closed_at` | TIMESTAMPTZ | When trade closed |
| `updated_at` | TIMESTAMPTZ | |

### Table: `webull_orders` (legacy)
Original Webull order tracking table. Still created in DB, no longer written to when using `BROKER=alpaca`. Kept for historical data preservation.

---

## 14. API Endpoints

Base path: `/api/v1`

### Health
```
GET  /health
→ { status: "ok", timestamp: "..." }
```

### Ingest (called by Discord agent, not end-user)
```
POST /ingest/alert
Body: { message_id, channel_id, author, content, embeds, timestamp, is_edit }
→ { accepted: true, signal_id: "uuid", action: "BUY" }
```

### Signals
```
GET  /signals?ticker=GOOGL&status=OPEN&limit=50&offset=0
→ { total: 5, signals: [...] }

GET  /signals/{signal_id}
→ ParsedSignal object
```

### Trades
```
GET  /trades?symbol=GOOGL&status=OPEN&limit=50
→ { total: 3, trades: [PaperTrade...] }

GET  /trades/summary
→ {
     total_trades: 12,
     open_trades: 2,
     closed_trades: 10,
     avg_pnl_pct: 8.3,
     total_pnl_dollars: 412.50
   }

GET  /trades/{trade_id}
→ Full PaperTrade with EMA/VWAP snapshot
```

Interactive docs: `http://localhost:8000/api/v1/openapi.json` or visit `http://localhost:8000/docs`

---

## 15. All Rules & Guard Checks

### Rule 1 — Master Kill-Switch
```
Setting:  EXECUTION_ENABLED=true/false
Default:  false
Checked:  First thing in Execution Agent, before ANY processing
Effect:   false → no trades, no WhatsApp, no Alpaca calls
```

### Rule 2 — Action Filter
```
Only BUY actions trigger trade execution.
EXIT, SELL, SL_HIT, SCALE_IN, SCALE_OUT, HOLD, UPDATE → all skipped.
These update the parsed_signal status (OPEN → CLOSED/PARTIAL) but don't trade.
```

### Rule 3 — Instrument Filter
```
Only STOCK and UNKNOWN contract types execute.
CALL and PUT → skipped with log "options not yet supported".
Reason: options require contract multiplier (100x), expiry, liquidity checks.
Future: add options support with separate sizing logic.
```

### Rule 4 — Market Hours
```
Setting:  MARKET_HOURS_ONLY=true/false
Default:  false (set true for production)
Window:   Mon–Fri, 09:30–16:00 Eastern Time
Effect:   Signals outside hours → skipped (not saved as CANCELLED)
Note:     Set false during testing so signals work at any time
```

### Rule 5 — EMA/VWAP Validation (all 4 must pass)
```
Check 1:  current_price > EMA9
Check 2:  current_price > EMA13
Check 3:  current_price > EMA21
Check 4:  current_price > VWAP

ANY check fails → trade CANCELLED, WhatsApp "Signal Skipped" sent.
ALL pass         → proceed to broker execution.
Data source:     Last 50 bars of 1-minute resolution (yfinance or Alpaca).
Minimum bars:    21 (to compute EMA21). Fewer → validation fails safely.
```

### Rule 6 — Take Profit (+15%)
```
Setting:      TAKE_PROFIT_PCT=0.15
Calculation:  tp_price = entry_price × 1.15
Executed by:  Alpaca as a LIMIT SELL order (bracket leg)
Trigger:      Alpaca auto-fills when market price reaches tp_price
DB record:    exit_reason=TP_HIT, pnl_pct=+15.x%
```

### Rule 7 — Stop Loss (-10%)
```
Setting:      STOP_LOSS_PCT=0.10
Calculation:  sl_price = entry_price × 0.90
Executed by:  Alpaca as a STOP SELL order (bracket leg)
Trigger:      Alpaca auto-fills when market price drops to sl_price
DB record:    exit_reason=SL_HIT, pnl_pct=-10.x%
```

### Rule 8 — Deduplication
```
Every incoming Discord message is checked against raw_alerts.message_id.
Already seen? → return (skip, no double-processing).
Edited message (is_edit=true)? → update existing raw_alert, re-process.
```

### Rule 9 — Position Size
```
Setting:  DEFAULT_QTY=1
Default:  1 share per signal
All trades execute with this quantity regardless of signal content.
Future: dynamic sizing based on account value / risk %.
```

### Rule 10 — Notification Failure Tolerance
```
WhatsApp send failures NEVER block or fail a trade.
All notifications are fire-and-forget asyncio tasks.
On Twilio error: logged at ERROR level, pipeline continues normally.
```

---

## 16. Environment Configuration (.env)

```bash
# ── App ───────────────────────────────────────────────
ENVIRONMENT=development
API_V1_STR=/api/v1

# ── Discord Self-Bot ───────────────────────────────────
DISCORD_USER_TOKEN=           # Your personal Discord token
DISCORD_TARGET_CHANNEL_IDS=  # Comma-separated channel IDs to monitor

# ── Database (PostgreSQL) ──────────────────────────────
DB_USER=linishareddy
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5433
DB_NAME=tradealert

# ── Broker selection (ONE LINE to swap) ───────────────
BROKER=alpaca                 # "alpaca" | "webull"

# ── Trade rules ────────────────────────────────────────
EXECUTION_ENABLED=true        # false = dry run (no trades placed)
TAKE_PROFIT_PCT=0.15          # 15% take profit
STOP_LOSS_PCT=0.10            # 10% stop loss
DEFAULT_QTY=1                 # shares per trade
MARKET_HOURS_ONLY=false       # true = only trade 9:30–16:00 ET

# ── Alpaca Paper Trading ───────────────────────────────
ALPACA_API_KEY=PKG...         # From alpaca.markets paper account
ALPACA_API_SECRET=68k...
ALPACA_PAPER=true             # false = real money (dangerous!)

# ── Market Data ────────────────────────────────────────
MARKET_DATA_PROVIDER=yfinance # "yfinance" | "alpaca"

# ── AI Parsing (Groq) ──────────────────────────────────
GROQ_API_KEY=gsk_...          # From console.groq.com
AI_PARSING_ENABLED=true

# ── WhatsApp Notifications (Twilio) ───────────────────
WHATSAPP_NOTIFICATIONS_ENABLED=true
TWILIO_ACCOUNT_SID=AC8...     # From twilio.com console
TWILIO_AUTH_TOKEN=eac...
TWILIO_WHATSAPP_FROM=+14155238886   # Twilio sandbox number
WHATSAPP_TO=+919666501513           # Your personal WhatsApp number
```

---

## 17. How to Swap Brokers

Change **one line** in `.env`:

```bash
# From Alpaca to Webull:
BROKER=webull

# Also add Webull credentials:
WEBULL_APP_KEY=your_key
WEBULL_APP_SECRET=your_secret
WEBULL_ACCOUNT_ID=your_account
WEBULL_ENDPOINT=us-openapi-alb.uat.webullbroker.com  # UAT sandbox
```

Restart the server. Zero code changes.

**Alpaca advantages:** Native bracket orders (1 API call), paper trading free, real-time data included.
**Webull advantages:** Direct integration with Webull account, institutional API.

---

## 18. How to Add a New Broker

Example: adding Interactive Brokers (IBKR).

**Step 1:** Create `services/v1/broker/ibkr_broker.py`
```python
from .port import BrokerPort
from .models import BracketOrderRequest, BrokerOrderResult, Position

class IBKRBroker(BrokerPort):
    async def place_bracket_order(self, req: BracketOrderRequest) -> BrokerOrderResult:
        # translate BracketOrderRequest → IBKR API call
        ...
    async def get_open_positions(self) -> list[Position]: ...
    async def get_order_status(self, broker_order_id: str) -> str: ...
    async def cancel_order(self, broker_order_id: str) -> bool: ...
```

**Step 2:** Add one case to `services/v1/broker/factory.py`
```python
case "ibkr":
    from .ibkr_broker import IBKRBroker
    _instance = IBKRBroker(host=settings.IBKR_HOST, port=settings.IBKR_PORT)
```

**Step 3:** Add settings to `config/settings.py` and `.env`
```python
IBKR_HOST: str = "127.0.0.1"
IBKR_PORT: int = 7497
```

**Step 4:** Set `.env`:
```bash
BROKER=ibkr
```

No other files need to change.

---

## 19. Error Handling Strategy

| Layer | Failure Type | Behaviour |
|---|---|---|
| Discord Agent | Network disconnect | `discord.py-self` auto-reconnects |
| Discord Agent | Invalid token | Logs "Invalid token", exits gracefully |
| Ingest HTTP | Server down | Agent logs failure, message lost (no retry) |
| Parsing | No format match + AI fails | Returns None, raw_alert still saved |
| Parsing AI | Groq API error | Logs warning, returns None, regex result used |
| EMA/VWAP | yfinance timeout | Returns ValidationResult(passed=False, reason="...") |
| EMA/VWAP | Too few bars | Returns ValidationResult(passed=False, reason="Only N bars...") |
| Execution | Alpaca API error | Logs error, returns None, CANCELLED paper_trade NOT saved |
| Execution | Broker credentials missing | Factory raises ValueError at startup |
| Monitor | Alpaca API down | Logs error, skips this cycle, retries next 60s |
| Monitor | Price fetch fails | Sets exit_reason=MANUAL, no pnl calculated |
| WhatsApp | Twilio API error | Logs error, trade pipeline continues unaffected |
| WhatsApp | Disabled/unconfigured | Returns False silently, no exception |
| Database | Connection lost | SQLAlchemy session closes, FastAPI returns 500 |

---

## 20. Running the System

### Start everything
```bash
cd /Users/yekaditya/Desktop/Trading_System/Trade-Alert
python3 main.py
```

This starts 3 concurrent asyncio tasks:
1. **FastAPI** server on `http://localhost:8000`
2. **Discord Agent** — watching channel `1515979604307742833`
3. **Monitor Agent** — polling Alpaca every 60 seconds

### Verify it's working
```bash
# Run end-to-end test (places + cancels a real Alpaca paper order)
python3 test_e2e.py

# Send test WhatsApp messages
python3 test_whatsapp.py
```

### View your trades
```
http://localhost:8000/api/v1/trades
http://localhost:8000/api/v1/trades/summary
http://localhost:8000/docs         ← Interactive API docs
```

### Logs to watch
```
[DiscordAgent]    ✅ Logged in as YourUsername#1234
[DiscordAgent]    ✅ Ready and listening for live messages...
[MonitorAgent]    ✅ Started — polling every 60s
[ParsingAgent]    ✅ format=D ticker=GOOGL action=BUY entry=368.0
[Validator]       GOOGL — passed=True price=368.03 ema9=367.80...
[ExecutionAgent]  ✅ Trade opened — ALPACA GOOGL x1 @ 368.03 | TP=423.23 SL=331.23
[WhatsApp]        ✅ Sent — SID=SMxxxxxxx
[MonitorAgent]    🔔 Trade CLOSED — GOOGL abc12345 | reason=TP_HIT | P&L=15.10%
```

### Turn off trading (dry run)
```bash
# In .env:
EXECUTION_ENABLED=false
```
Messages still parse and validate, but no orders are placed and no WhatsApp notifications are sent.

### Switch to real money (when ready)
```bash
ALPACA_PAPER=false          # switch Alpaca to live account
EXECUTION_ENABLED=true
MARKET_HOURS_ONLY=true      # only trade during market hours
```

---

*This document covers the complete system as of June 2026. All 5 agents, 2 port layers, 4 database tables, 5 WhatsApp templates, and all 10 guard rules are described above.*
