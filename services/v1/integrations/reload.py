"""
Apply integration credential changes without a full backend restart.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

_DISCORD_KEYS = {"discord_token", "discord_channels"}
_ALPACA_KEYS = {"alpaca_key", "alpaca_secret"}
_GROQ_KEYS = {"groq_key"}


def apply_integration_reload(changed_keys: set[str]) -> None:
    """Hot-reload services affected by updated integration credentials."""
    if changed_keys & _DISCORD_KEYS:
        from agents.discord.discord_agent import request_discord_reconnect
        request_discord_reconnect()
        logger.info("[Integrations] Discord reconnect requested")

    if changed_keys & _ALPACA_KEYS:
        from services.v1.broker.factory import reset_broker
        from services.v1.market_data.factory import reset_market_data
        reset_broker()
        reset_market_data()
        logger.info("[Integrations] Alpaca broker + market data reset")

    if changed_keys & _GROQ_KEYS:
        logger.info("[Integrations] Groq key updated — next AI parse uses new key")
