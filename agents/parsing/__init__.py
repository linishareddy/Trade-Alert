"""
parsing/__init__.py

Regex-based parsing agent for Discord trading alerts.
Falls back to Groq LLM when no regex format matches.

Format A — Shorthand options (BTO/STC):
    BTO $SBUX 103c 06/12 @0.55

Format B — Index / spread block (2 lines):
    SPXW PUT 8.70
    260610 7275.00 8.50

Format C — Structured Discord embed:
    title: "Entry"
    fields: Contract: QQQ $742c | Price: $2.05

Format D — Plain-text stock/options trade:
    Buy TSLA @ 250, TP 270, SL 245
    Sell $AAPL @ 180 SL 185 TP 170
    BTO SPY 450c @ 1.50
"""
from __future__ import annotations
import asyncio
import json
import re
import logging
from datetime import date, datetime

from models.v1.parsing.parsed_signal_dto import ParsedSignalDTO

logger = logging.getLogger(__name__)


# ── Action keyword map ────────────────────────────────────────────────────────

_ACTION_MAP: dict[str, str] = {
    "BTO": "BUY",
    "STC": "EXIT",
    "BUY": "BUY",
    "LONG": "BUY",
    "ENTRY": "BUY",
    "SELL": "SELL",
    "SHORT": "SELL",
    "EXIT": "EXIT",
    "CLOSE": "EXIT",
    "STOP LOSS HIT": "SL_HIT",
    "SL HIT": "SL_HIT",
    "SCALE IN": "SCALE_IN",
    "SCALE OUT": "SCALE_OUT",
    "HOLD": "HOLD",
    "UPDATE": "UPDATE",
}

_FOLLOWUP_ACTIONS = {"EXIT", "SL_HIT", "SCALE_IN", "SCALE_OUT", "HOLD", "UPDATE"}


# ── Format A ─────────────────────────────────────────────────────────────────
# Example: BTO $SBUX 103c 06/12 @0.55
#          STC $AAPL 180p 12/15/26 @2.10

_FORMAT_A = re.compile(
    r"^(BTO|STC)\s+"               # action keyword
    r"\$?([A-Z]{1,6})\s+"          # $TICKER or TICKER
    r"(\d+\.?\d*)(c|p)\s+"         # strikeC or strikeP
    r"(\d{2}/\d{2}(?:/\d{2,4})?)"  # expiry MM/DD or MM/DD/YY or MM/DD/YYYY
    r"\s+@(\d+\.?\d*)",            # @price
    re.IGNORECASE,
)


def _parse_format_a(content: str) -> ParsedSignalDTO | None:
    m = _FORMAT_A.match(content.strip())
    if not m:
        return None

    raw_action, ticker, strike_str, cp, expiry_str, price_str = m.groups()
    action = _ACTION_MAP.get(raw_action.upper(), "BUY")
    contract_type = "CALL" if cp.lower() == "c" else "PUT"
    expiry = _parse_expiry_slash(expiry_str)

    return ParsedSignalDTO(
        action=action,
        ticker=ticker.upper(),
        contract_type=contract_type,
        strike=float(strike_str),
        expiry=expiry,
        entry_price=float(price_str),
        is_followup=action in _FOLLOWUP_ACTIONS,
        parse_format="A",
    )


# ── Format B ─────────────────────────────────────────────────────────────────
# Example (2 lines):
#   SPXW PUT 8.70
#   260610 7275.00 8.50

_FORMAT_B_LINE1 = re.compile(
    r"^([A-Z]{2,6})\s+(CALL|PUT)\s+(\d+\.?\d*)",
    re.IGNORECASE,
)
_FORMAT_B_LINE2 = re.compile(
    r"^(\d{6})\s+(\d+\.?\d*)\s+(\d+\.?\d*)"
)


def _parse_format_b(content: str) -> ParsedSignalDTO | None:
    lines = [l.strip() for l in content.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return None

    m1 = _FORMAT_B_LINE1.match(lines[0])
    m2 = _FORMAT_B_LINE2.match(lines[1])
    if not m1 or not m2:
        return None

    ticker, cp, price_str = m1.groups()
    expiry_str, strike_str, sl_str = m2.groups()

    contract_type = "CALL" if cp.upper() == "CALL" else "PUT"
    expiry = _parse_expiry_yymmdd(expiry_str)

    return ParsedSignalDTO(
        action="BUY",
        ticker=ticker.upper(),
        contract_type=contract_type,
        strike=float(strike_str),
        expiry=expiry,
        entry_price=float(price_str),
        stop_loss=float(sl_str),
        is_followup=False,
        parse_format="B",
    )


# ── Format C ─────────────────────────────────────────────────────────────────
# Structured Discord embed with title + fields
# title: "Entry" / "Exit" / "Stop Loss Hit"
# fields: Contract: QQQ $742c | Price: $2.05

_CONTRACT_FIELD = re.compile(
    r"\$?([A-Z]{1,6})\s+\$?(\d+\.?\d*)(c|p)",
    re.IGNORECASE,
)
_PRICE_FIELD = re.compile(r"\$?(\d+\.?\d*)")


def _parse_format_c(content: str, embeds: list[dict]) -> ParsedSignalDTO | None:
    if not embeds:
        return None

    for embed in embeds:
        title = (embed.get("title") or "").strip().upper()
        action = _ACTION_MAP.get(title, None)
        if not action:
            continue  # Only process embeds with known action titles

        fields: dict[str, str] = {}
        for f in embed.get("fields", []):
            fields[f.get("name", "").strip().lower()] = f.get("value", "").strip()

        # Parse contract field: e.g. "QQQ $742c"
        contract_raw = fields.get("contract", "")
        mc = _CONTRACT_FIELD.search(contract_raw)
        if not mc:
            continue

        ticker, strike_str, cp = mc.groups()
        contract_type = "CALL" if cp.lower() == "c" else "PUT"

        # Parse price field: e.g. "$2.05"
        price_raw = fields.get("price", "")
        mp = _PRICE_FIELD.search(price_raw)
        entry_price = float(mp.group(1)) if mp else None

        return ParsedSignalDTO(
            action=action,
            ticker=ticker.upper(),
            contract_type=contract_type,
            strike=float(strike_str),
            entry_price=entry_price,
            is_followup=action in _FOLLOWUP_ACTIONS,
            parse_format="C",
        )

    return None


# ── Format D ─────────────────────────────────────────────────────────────────
# Plain-text natural language stock/options trades
# Examples:
#   Buy TSLA @ 250, TP 270, SL 245
#   Sell $AAPL @ 180 SL 185 TP 170
#   BTO SPY 450c @ 1.50
#   Long $NVDA @ 120

# Leading action word
_FORMAT_D_ACTION = re.compile(
    r"^(BTO|STC|BUY|SELL|LONG|SHORT|EXIT|CLOSE|HOLD|SCALE\s*IN|SCALE\s*OUT)\b",
    re.IGNORECASE,
)
# Ticker: $AAPL or plain uppercase AAPL/TSLA
_FORMAT_D_TICKER = re.compile(r"\$([A-Z]{1,6})|(?<!\d)([A-Z]{2,6})(?!\d)")
# Optional options suffix on ticker: 450c or 180p
_FORMAT_D_OPTION = re.compile(r"(\d+\.?\d*)(c|p)\b", re.IGNORECASE)
# Entry price: @ 250 or @ 1.50
_FORMAT_D_ENTRY = re.compile(r"@\s*(\d+\.?\d*)")
# TP: TP 270 or target 270
_FORMAT_D_TP = re.compile(r"\b(?:TP|TARGET|TAKE\s*PROFIT)\s*[:\s]\s*(\d+\.?\d*)", re.IGNORECASE)
# SL: SL 245 or stop 245
_FORMAT_D_SL = re.compile(r"\b(?:SL|STOP(?:\s*LOSS)?)\s*[:\s]?\s*(\d+\.?\d*)", re.IGNORECASE)

# Words that look like tickers but are noise
_TICKER_NOISE = {
    "BTO", "STC", "BUY", "SELL", "LONG", "SHORT", "EXIT", "CLOSE",
    "HOLD", "UPDATE", "TP", "SL", "AT", "OR", "IN", "ON", "IS",
    "THE", "AND", "FOR", "STOP", "LOSS", "TAKE", "PROFIT", "TARGET",
    "SCALE", "ENTRY", "ALERT", "BELOW", "ABOVE",
}


def _parse_format_d(content: str) -> ParsedSignalDTO | None:
    text = content.strip()

    # Must start with a known action word
    am = _FORMAT_D_ACTION.match(text)
    if not am:
        return None

    raw_action = am.group(1).upper().replace(" ", "_")
    # Normalise SCALE_IN / SCALE_OUT
    action = _ACTION_MAP.get(raw_action.replace("_", " "), _ACTION_MAP.get(raw_action, "UPDATE"))

    # Extract entry price
    entry_m = _FORMAT_D_ENTRY.search(text)
    entry_price = float(entry_m.group(1)) if entry_m else None

    # Extract TP / SL
    tp_m = _FORMAT_D_TP.search(text)
    target_price = float(tp_m.group(1)) if tp_m else None

    sl_m = _FORMAT_D_SL.search(text)
    stop_loss = float(sl_m.group(1)) if sl_m else None

    # Check for inline options suffix (e.g. "SPY 450c")
    opt_m = _FORMAT_D_OPTION.search(text)
    if opt_m:
        strike = float(opt_m.group(1))
        contract_type = "CALL" if opt_m.group(2).lower() == "c" else "PUT"
    else:
        strike = None
        contract_type = "STOCK"

    # Extract ticker — prefer $TICKER, fallback to uppercase word
    ticker: str | None = None
    dollar_m = re.search(r"\$([A-Z]{1,6})\b", text)
    if dollar_m:
        ticker = dollar_m.group(1).upper()
    else:
        # Find all UPPERCASE words after the action word, skip noise
        words = re.findall(r"\b([A-Z]{2,6})\b", text.upper())
        for w in words:
            if w not in _TICKER_NOISE:
                ticker = w
                break

    if not ticker:
        return None

    return ParsedSignalDTO(
        action=action,
        ticker=ticker,
        contract_type=contract_type,
        strike=strike,
        entry_price=entry_price,
        target_price=target_price,
        stop_loss=stop_loss,
        is_followup=action in _FOLLOWUP_ACTIONS,
        parse_format="D",
    )


# ── Expiry parsers ────────────────────────────────────────────────────────────

def _parse_expiry_slash(s: str) -> date | None:
    """Parse MM/DD, MM/DD/YY, or MM/DD/YYYY."""
    now = datetime.utcnow()
    parts = s.split("/")
    try:
        if len(parts) == 2:
            month, day = int(parts[0]), int(parts[1])
            year = now.year
            if date(year, month, day) < now.date():
                year += 1
            return date(year, month, day)
        elif len(parts) == 3:
            month, day = int(parts[0]), int(parts[1])
            raw_year = int(parts[2])
            year = 2000 + raw_year if raw_year < 100 else raw_year
            return date(year, month, day)
    except ValueError:
        pass
    return None


def _parse_expiry_yymmdd(s: str) -> date | None:
    """Parse YYMMDD format, e.g. 260610 → 2026-06-10."""
    if len(s) != 6:
        return None
    try:
        year = 2000 + int(s[:2])
        month = int(s[2:4])
        day = int(s[4:6])
        return date(year, month, day)
    except ValueError:
        return None


# ── Public entry points ───────────────────────────────────────────────────────

def parse(content: str, embeds: list[dict]) -> ParsedSignalDTO | None:
    """
    Synchronous regex-only parse. Try each format in priority order.
    Priority: A → B → C → D
    Returns None if nothing matches (caller should use parse_async instead).
    """
    return (
        _parse_format_a(content)
        or _parse_format_b(content)
        or _parse_format_c(content, embeds)
        or _parse_format_d(content)
    )


async def parse_async(content: str, embeds: list[dict]) -> ParsedSignalDTO | None:
    """
    Async entry point used by ingestion_service.
    Tries regex first (fast, free). If all fail, falls back to Groq LLM.
    """
    result = parse(content, embeds)

    if result:
        logger.info(
            "[ParsingAgent] ✅ regex format=%s ticker=%s action=%s entry=%s",
            result.parse_format, result.ticker, result.action, result.entry_price,
        )
        return result

    # ── AI fallback ───────────────────────────────────────────────────────────
    from config.settings import settings
    if settings.AI_PARSING_ENABLED and settings.GROQ_API_KEY:
        logger.info("[ParsingAgent] Regex failed — trying Groq AI fallback")
        result = await _parse_with_ai(content, embeds)
        if result:
            logger.info(
                "[ParsingAgent] ✅ AI format=%s ticker=%s action=%s entry=%s",
                result.parse_format, result.ticker, result.action, result.entry_price,
            )
            return result

    logger.warning("[ParsingAgent] ⚠ No format matched (regex + AI): %r", content[:120])
    return None


async def _parse_with_ai(content: str, embeds: list[dict]) -> ParsedSignalDTO | None:
    """Use Groq (Llama 3) to extract a structured signal from any message format."""
    from groq import Groq
    from config.settings import settings

    embed_text = ""
    if embeds:
        embed_text = f"\nEmbeds: {json.dumps(embeds[:1], default=str)[:400]}"

    prompt = f"""You extract trading signals from Discord messages. Return JSON only, no explanation.

Message: {content[:600]}{embed_text}

Return EXACTLY this JSON (use null for unknown fields):
{{
  "action": "BUY|SELL|EXIT|SL_HIT|SCALE_IN|SCALE_OUT|HOLD|UPDATE",
  "ticker": "AAPL",
  "contract_type": "STOCK|CALL|PUT|UNKNOWN",
  "strike": null,
  "expiry": null,
  "entry_price": 150.00,
  "target_price": null,
  "stop_loss": null
}}

If this message is NOT a trading signal, return: {{"action": null}}"""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=250,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        if not data.get("action"):
            return None

        action = data["action"].upper()
        ticker = (data.get("ticker") or "").upper().strip()
        if not ticker:
            return None

        return ParsedSignalDTO(
            action=action,
            ticker=ticker,
            contract_type=data.get("contract_type", "UNKNOWN") or "UNKNOWN",
            strike=float(data["strike"]) if data.get("strike") else None,
            expiry=None,  # date parsing from AI string is fragile — leave for future
            entry_price=float(data["entry_price"]) if data.get("entry_price") else None,
            target_price=float(data["target_price"]) if data.get("target_price") else None,
            stop_loss=float(data["stop_loss"]) if data.get("stop_loss") else None,
            is_followup=action in _FOLLOWUP_ACTIONS,
            parse_format="AI",
        )

    except Exception as exc:
        logger.warning("[ParsingAgent] Groq AI parse failed: %s", exc)
        return None
