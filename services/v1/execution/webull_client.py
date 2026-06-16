"""
webull_client.py

Lazy singleton wrapper around the official Webull OpenAPI Python SDK.

SDK package: webull-openapi-python-sdk
Install:     pip install webull-openapi-python-sdk

The client is initialised on first use and reused for all subsequent calls.
If credentials are not configured, get_trade_client() raises RuntimeError so
the Execution Agent can disable itself cleanly without crashing the server.
"""
from __future__ import annotations
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

_trade_client = None  # lazy singleton


def get_trade_client():
    """
    Return a live Webull TradeApi instance.
    Raises RuntimeError if WEBULL_APP_KEY / WEBULL_APP_SECRET are not set.
    """
    global _trade_client

    if _trade_client is not None:
        return _trade_client

    if not settings.WEBULL_APP_KEY or not settings.WEBULL_APP_SECRET:
        raise RuntimeError(
            "Webull credentials not configured. "
            "Set WEBULL_APP_KEY and WEBULL_APP_SECRET in your .env file."
        )

    try:
        from webullsdkcore.client import ApiClient
        from webullsdktrade.api.trade_api import TradeApi
    except ImportError:
        raise RuntimeError(
            "Webull SDK not installed. Run: pip install webull-openapi-python-sdk"
        )

    api_client = ApiClient(
        app_key=settings.WEBULL_APP_KEY,
        app_secret=settings.WEBULL_APP_SECRET,
    )
    api_client.set_env("us", settings.WEBULL_ENDPOINT)
    logger.info(
        "[WebullClient] Initialised — endpoint=%s account=%s",
        settings.WEBULL_ENDPOINT,
        settings.WEBULL_ACCOUNT_ID,
    )
    _trade_client = TradeApi(api_client)
    return _trade_client
