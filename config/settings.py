from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # ── Database ───────────────────────────────────────────────────────────────
    DB_USER: str = "linishareddy"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "tradealert"

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        if self.DB_PASSWORD:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"postgresql+asyncpg://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ── Discord self-bot ───────────────────────────────────────────────────────
    DISCORD_USER_TOKEN: str = ""
    DISCORD_TARGET_CHANNEL_IDS: str = ""

    # Internal ingest endpoint (agent → backend)
    INGEST_URL: str = "http://127.0.0.1:8000/api/v1/ingest/alert"

    # ── Broker selection (change ONE line to swap brokers) ─────────────────────
    # Options: "alpaca" | "webull"
    BROKER: str = "alpaca"

    # ── Trade rules (apply to ALL brokers) ────────────────────────────────────
    EXECUTION_ENABLED: bool = False       # master kill-switch
    TAKE_PROFIT_PCT: float = 0.15         # 15% profit target
    STOP_LOSS_PCT: float = 0.10           # 10% stop loss
    DEFAULT_QTY: int = 1                  # shares per signal
    MARKET_HOURS_ONLY: bool = True        # skip signals outside 9:30–16:00 ET

    # ── Alpaca ─────────────────────────────────────────────────────────────────
    ALPACA_API_KEY: str = ""
    ALPACA_API_SECRET: str = ""
    ALPACA_PAPER: bool = True             # False = live money

    # ── Market data provider ───────────────────────────────────────────────────
    # Options: "yfinance" | "alpaca"
    MARKET_DATA_PROVIDER: str = "yfinance"

    # ── AI Parsing (Groq fallback) ─────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    AI_PARSING_ENABLED: bool = True

    # ── WhatsApp Notifications (Twilio) ───────────────────────────────────────
    WHATSAPP_NOTIFICATIONS_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""   # Twilio sandbox/production number e.g. +14155238886
    WHATSAPP_TO: str = ""            # Your personal WhatsApp number e.g. +919666501513

    # ── Webull OpenAPI (kept for when you switch BROKER=webull) ───────────────
    WEBULL_APP_KEY: str = ""
    WEBULL_APP_SECRET: str = ""
    WEBULL_ACCOUNT_ID: str = ""
    WEBULL_ENDPOINT: str = "us-openapi-alb.uat.webullbroker.com"

    # Legacy fields (kept so existing .env files don't break)
    WEBULL_EXECUTION_ENABLED: bool = False
    WEBULL_DEFAULT_QTY: int = 1
    WEBULL_ORDER_TYPE: str = "LIMIT"
    WEBULL_MARKET_HOURS_ONLY: bool = True

    @property
    def discord_channel_ids(self) -> list[int]:
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
