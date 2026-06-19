"""
Market data factory — returns the configured MarketDataPort adapter.
Change MARKET_DATA_PROVIDER in .env to swap without code changes.
"""
from __future__ import annotations
from .port import MarketDataPort

_instance: MarketDataPort | None = None


def get_market_data() -> MarketDataPort:
    global _instance
    if _instance is not None:
        return _instance

    from config.settings import settings

    match settings.MARKET_DATA_PROVIDER.lower():
        case "yfinance":
            from .yfinance_adapter import YFinanceData
            _instance = YFinanceData()
        case "alpaca":
            from .alpaca_data_adapter import AlpacaData
            _instance = AlpacaData(
                api_key=settings.ALPACA_API_KEY,
                api_secret=settings.ALPACA_API_SECRET,
            )
        case other:
            raise ValueError(
                f"Unknown market data provider '{other}'. "
                "Valid options: yfinance, alpaca."
            )

    return _instance


def reset_market_data() -> None:
    global _instance
    _instance = None
