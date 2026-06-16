"""
parsing_agent.py

Regex-based parsing agent for Discord trading alerts.

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


# ── Public entry point ────────────────────────────────────────────────────────

def parse(content: str, embeds: list[dict]) -> ParsedSignalDTO | None:
    """
    Try each format in priority order, return the first match.

    Priority: A → B → C → D (plain-text fallback)
    Returns None if no format matches.
    """
    result = (
        _parse_format_a(content)
        or _parse_format_b(content)
        or _parse_format_c(content, embeds)
        or _parse_format_d(content)
    )
    if result:
        logger.info(
            "[ParsingAgent] ✅ format=%s ticker=%s action=%s "
            "contract=%s strike=%s expiry=%s entry=%s tp=%s sl=%s",
            result.parse_format, result.ticker, result.action,
            result.contract_type, result.strike, result.expiry,
            result.entry_price, result.target_price, result.stop_loss,
        )
    else:
        logger.warning("[ParsingAgent] ⚠ No format matched: %r", content[:120])
    return result
