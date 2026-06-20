"""
runtime_settings.py

DB-backed runtime config layer. On every read, DB overrides take priority
over .env values. Writes go to DB immediately and update the in-memory cache.

Usage:
    from services.v1.config.runtime_settings import runtime

    # Read (synchronous — uses in-memory cache)
    enabled = runtime.get("execution_enabled")

    # Write (async — persists to DB then updates cache)
    await runtime.set("execution_enabled", False, db_session)
"""
from __future__ import annotations
from typing import Any
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# ── Key → (settings attr name, Python type) ──────────────────────────────────
# Only these keys can be changed at runtime via PATCH /config.
EDITABLE: dict[str, tuple[str, type]] = {
    # ── Runtime toggles / numbers ──────────────────────────────────────────────
    "execution_enabled":  ("EXECUTION_ENABLED",               bool),
    "ema_vwap_enabled":   ("EMA_VWAP_ENABLED",                bool),
    "market_hours_only":  ("MARKET_HOURS_ONLY",               bool),
    "ai_parsing_enabled": ("AI_PARSING_ENABLED",              bool),
    "whatsapp_enabled":   ("WHATSAPP_NOTIFICATIONS_ENABLED",  bool),
    "take_profit_pct":    ("TAKE_PROFIT_PCT",                 float),
    "stop_loss_pct":      ("STOP_LOSS_PCT",                   float),
    "default_qty":        ("DEFAULT_QTY",                     int),
    "ai_model":           ("AI_MODEL",                        str),
    # ── Integration credentials (stored in DB, override .env at runtime) ───────
    "discord_token":      ("DISCORD_USER_TOKEN",              str),
    "discord_channels":   ("DISCORD_TARGET_CHANNEL_IDS",      str),
    "twilio_sid":         ("TWILIO_ACCOUNT_SID",              str),
    "twilio_token":       ("TWILIO_AUTH_TOKEN",               str),
    "twilio_from":        ("TWILIO_WHATSAPP_FROM",            str),
    "whatsapp_to":        ("WHATSAPP_TO",                     str),
    "groq_key":           ("GROQ_API_KEY",                    str),
    "alpaca_key":         ("ALPACA_API_KEY",                  str),
    "alpaca_secret":      ("ALPACA_API_SECRET",               str),
}


def _coerce(raw: str, type_fn: type) -> Any:
    """Convert a string value from DB to the correct Python type."""
    if type_fn is bool:
        return raw.lower() in ("true", "1", "yes")
    return type_fn(raw)


class _RuntimeSettings:
    """Singleton that wraps `settings` with DB overrides."""

    def __init__(self) -> None:
        self._overrides: dict[str, Any] = {}

    # ── Startup ───────────────────────────────────────────────────────────────

    async def load(self, db: AsyncSession) -> None:
        """Load all DB overrides into memory. Call once at app startup."""
        from db.models.system_config import SystemConfig
        rows = await db.execute(select(SystemConfig))
        for row in rows.scalars().all():
            if row.key in EDITABLE:
                _, type_fn = EDITABLE[row.key]
                self._overrides[row.key] = _coerce(row.value, type_fn)
        logger.info("[RuntimeSettings] Loaded %d override(s) from DB", len(self._overrides))

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, key: str) -> Any:
        """Return the runtime value — DB override wins over .env."""
        if key in self._overrides:
            val = self._overrides[key]
            _, type_fn = EDITABLE[key]
            # Empty string saved from Integrations UI should not block .env defaults
            if type_fn is str and val == "":
                return self.env_get(key)
            return val
        return self.env_get(key)

    def env_get(self, key: str) -> Any:
        """Return the .env default only (ignores DB overrides)."""
        from config.settings import settings
        settings_attr, _ = EDITABLE[key]
        return getattr(settings, settings_attr)

    def is_overridden(self, key: str) -> bool:
        """True when this key has a DB override active."""
        return key in self._overrides

    # ── Write ─────────────────────────────────────────────────────────────────

    async def set(self, key: str, value: Any, db: AsyncSession) -> None:
        """Persist an override to DB and update in-memory cache."""
        from db.models.system_config import SystemConfig
        from datetime import datetime, timezone

        if key not in EDITABLE:
            raise ValueError(f"Key '{key}' is not editable at runtime")

        _, type_fn = EDITABLE[key]
        typed_value = type_fn(value)

        # Upsert
        existing = await db.get(SystemConfig, key)
        if existing:
            existing.value = str(typed_value)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(SystemConfig(key=key, value=str(typed_value)))

        await db.commit()
        self._overrides[key] = typed_value
        logger.info("[RuntimeSettings] %s → %s", key, typed_value)

    # ── Delete (reset to .env) ────────────────────────────────────────────────

    async def reset(self, key: str, db: AsyncSession) -> None:
        """Remove DB override — value falls back to .env."""
        from db.models.system_config import SystemConfig
        row = await db.get(SystemConfig, key)
        if row:
            await db.delete(row)
            await db.commit()
        self._overrides.pop(key, None)
        logger.info("[RuntimeSettings] %s reset to .env default", key)


# ── Module-level singleton ────────────────────────────────────────────────────
runtime = _RuntimeSettings()
