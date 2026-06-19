"""
Broker factory — returns the configured BrokerPort adapter.

Change BROKER in .env to swap brokers with zero code changes.
Adding a new broker: implement BrokerPort, add one `case` below.
"""
from __future__ import annotations
from .port import BrokerPort

_instance: BrokerPort | None = None


def get_broker() -> BrokerPort:
    global _instance
    if _instance is not None:
        return _instance

    from config.settings import settings

    match settings.BROKER.lower():
        case "alpaca":
            from .alpaca_broker import AlpacaBroker
            _instance = AlpacaBroker(
                api_key=settings.ALPACA_API_KEY,
                api_secret=settings.ALPACA_API_SECRET,
                paper=settings.ALPACA_PAPER,
            )
        case "webull":
            from .webull_broker import WebullBroker
            _instance = WebullBroker(
                app_key=settings.WEBULL_APP_KEY,
                app_secret=settings.WEBULL_APP_SECRET,
                account_id=settings.WEBULL_ACCOUNT_ID,
                endpoint=settings.WEBULL_ENDPOINT,
            )
        case other:
            raise ValueError(
                f"Unknown broker '{other}'. "
                "Valid options: alpaca, webull. "
                "Set BROKER=<name> in .env and add a case to factory.py."
            )

    return _instance


def reset_broker() -> None:
    """Force re-initialisation on next call (useful in tests)."""
    global _instance
    _instance = None
