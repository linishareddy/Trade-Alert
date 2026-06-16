from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Database — individual parts assembled into DATABASE_URL
    DB_USER: str = "linishareddy"
    DB_PASSWORD: str = ""              # empty = no password (local Homebrew default)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "tradealert"

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        if self.DB_PASSWORD:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+asyncpg://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Discord self-bot
    DISCORD_USER_TOKEN: str = ""
    DISCORD_TARGET_CHANNEL_IDS: str = ""  # raw comma-separated string from .env

    # Internal ingest endpoint (agent → backend)
    INGEST_URL: str = "http://127.0.0.1:8000/api/v1/ingest/alert"

    # ── Webull OpenAPI ─────────────────────────────────────────────────────────
    WEBULL_APP_KEY: str = ""
    WEBULL_APP_SECRET: str = ""
    WEBULL_ACCOUNT_ID: str = ""

    # UAT sandbox: "us-openapi-alb.uat.webullbroker.com"
    # Production:  "us-openapi-alb.webullbroker.com"
    WEBULL_ENDPOINT: str = "us-openapi-alb.uat.webullbroker.com"

    # Master kill-switch — set to "true" only when ready to trade real money
    WEBULL_EXECUTION_ENABLED: bool = False

    # Default quantity (shares for stocks, contracts for options) per signal
    WEBULL_DEFAULT_QTY: int = 1

    # "LIMIT" uses entry_price from signal; "MARKET" fills immediately at best price
    WEBULL_ORDER_TYPE: str = "LIMIT"

    # Block orders outside regular market hours (9:30-16:00 ET)
    WEBULL_MARKET_HOURS_ONLY: bool = True

    @property
    def discord_channel_ids(self) -> list[int]:
        """Parse DISCORD_TARGET_CHANNEL_IDS into a list of ints."""
        if not self.DISCORD_TARGET_CHANNEL_IDS:
            return []
        return [int(c.strip()) for c in self.DISCORD_TARGET_CHANNEL_IDS.split(",") if c.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
