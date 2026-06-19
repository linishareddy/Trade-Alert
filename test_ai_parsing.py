"""
test_ai_parsing.py — AI parsing (Groq) smoke test

Run:
  python test_ai_parsing.py
  python test_ai_parsing.py "your custom discord message here"

Checks:
  1. Config (AI_PARSING_ENABLED, GROQ_API_KEY, AI_MODEL)
  2. Regex path still works (no Groq call needed)
  3. AI fallback on messages regex cannot parse
  4. Non-signal messages return None
"""
from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, ".")


# Messages regex should handle — AI must NOT be used
REGEX_CASES: list[tuple[str, str]] = [
    ("Buy GOOGL @ 368, SL 331, TP 423", "D"),
    ("BTO $AAPL 180c 12/15 @2.10", "A"),
]

# Messages regex cannot parse — Groq AI fallback should handle
AI_CASES: list[str] = [
    "just bought GOOGL here around 368 holding with stop at 331",
    "🚀 NVDA looking strong — entry ~950, stop 900, targeting 1050",
    "Scaling into TSLA, picked up shares near 245",
]

# Should NOT be treated as a trade signal
NON_SIGNAL_CASES: list[str] = [
    "good morning everyone, market looks choppy today",
    "remember to manage risk and stay disciplined",
]


def _print_result(label: str, msg: str, result) -> bool:
    preview = msg if len(msg) <= 70 else msg[:67] + "..."
    if result is None:
        print(f"  ❌ {label}: no parse result")
        print(f"     msg: {preview!r}")
        return False

    print(
        f"  ✅ {label}: format={result.parse_format} action={result.action} "
        f"ticker={result.ticker} entry={result.entry_price} sl={result.stop_loss}"
    )
    print(f"     msg: {preview!r}")
    return True


async def test_config() -> bool:
    from config.settings import settings

    print("=" * 60)
    print("  AI Parsing Test")
    print("=" * 60)
    print(f"  AI_PARSING_ENABLED = {settings.AI_PARSING_ENABLED}")
    print(f"  AI_MODEL           = {settings.AI_MODEL}")
    print(f"  GROQ_API_KEY       = {'set (' + settings.GROQ_API_KEY[:8] + '...)' if settings.GROQ_API_KEY else 'MISSING'}")

    if not settings.AI_PARSING_ENABLED:
        print("\n  ❌ AI_PARSING_ENABLED=false — enable it in .env to test AI fallback.")
        return False
    if not settings.GROQ_API_KEY:
        print("\n  ❌ GROQ_API_KEY missing — add it to .env.")
        return False

    print("  ✅ Config OK\n")
    return True


async def test_regex_path() -> bool:
    import agents.parsing as parsing

    print("── Regex path (Groq should NOT run) ──")
    ok = True
    for msg, expected_fmt in REGEX_CASES:
        result = await parsing.parse_async(msg, [])
        if not result or result.parse_format != expected_fmt:
            ok = False
            _print_result(f"expected {expected_fmt}", msg, result)
        else:
            _print_result(expected_fmt, msg, result)
    print()
    return ok


async def test_ai_fallback() -> bool:
    import agents.parsing as parsing

    print("── AI fallback (regex fails → Groq) ──")
    ok = True
    for msg in AI_CASES:
        # Confirm regex alone fails
        regex_only = parsing.parse(msg, [])
        if regex_only:
            print(f"  ⚠️  Skipping (regex matched unexpectedly): {msg[:60]!r}")
            continue

        result = await parsing.parse_async(msg, [])
        if not result or result.parse_format != "AI":
            ok = False
            _print_result("expected AI", msg, result)
        else:
            _print_result("AI", msg, result)
    print()
    return ok


async def test_non_signals() -> bool:
    import agents.parsing as parsing

    print("── Non-signals (should return None) ──")
    ok = True
    for msg in NON_SIGNAL_CASES:
        result = await parsing.parse_async(msg, [])
        if result is not None:
            ok = False
            print(f"  ❌ Should be None but got: {result.action} {result.ticker}")
            print(f"     msg: {msg!r}")
        else:
            print(f"  ✅ Correctly ignored: {msg!r}")
    print()
    return ok


async def test_custom_message(msg: str) -> bool:
    import agents.parsing as parsing

    print("── Custom message ──")
    regex_only = parsing.parse(msg, [])
    if regex_only:
        print(f"  ℹ️  Regex matched first: format={regex_only.parse_format}")
        _print_result(regex_only.parse_format, msg, regex_only)
        return True

    result = await parsing.parse_async(msg, [])
    if result:
        _print_result(result.parse_format, msg, result)
        return True

    _print_result("none", msg, result)
    return False


async def main() -> None:
    if not await test_config():
        sys.exit(1)

    custom = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""

    if custom:
        ok = await test_custom_message(custom)
        print("=" * 60)
        print("  Result:", "PASS ✅" if ok else "FAIL ❌")
        print("=" * 60)
        sys.exit(0 if ok else 1)

    results = [
        await test_regex_path(),
        await test_ai_fallback(),
        await test_non_signals(),
    ]

    all_ok = all(results)
    print("=" * 60)
    print("  Summary")
    print(f"  Regex path:   {'PASS ✅' if results[0] else 'FAIL ❌'}")
    print(f"  AI fallback:  {'PASS ✅' if results[1] else 'FAIL ❌'}")
    print(f"  Non-signals:  {'PASS ✅' if results[2] else 'FAIL ❌'}")
    print()
    print("  Tip: python test_ai_parsing.py \"your discord alert text\"")
    print("=" * 60)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
