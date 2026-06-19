from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str


class ConfigResponse(BaseModel):
    # Broker & Execution
    broker: str
    alpaca_paper: bool
    execution_enabled: bool
    ema_vwap_enabled: bool
    market_hours_only: bool
    market_open: str
    market_close: str
    # Trade rules
    take_profit_pct: float
    stop_loss_pct: float
    default_qty: int
    # Validation
    ema_periods: str
    bar_lookback: int
    bar_minutes: int
    supported_contracts: str
    # Data & AI
    market_data_provider: str
    ai_parsing_enabled: bool
    ai_model: str
    # Notifications
    whatsapp_enabled: bool
    # DB / env (read-only)
    db_host: str
    db_port: int
    db_name: str
    environment: str


class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any


class ConfigUpdateResponse(BaseModel):
    key: str
    value: Any
    config: ConfigResponse


class ConfigResetResponse(BaseModel):
    key: str
    config: ConfigResponse


class GroqModel(BaseModel):
    id: str
    name: str
    speed: str           # "fast" | "medium" | "slow"
    context_k: int       # context window in thousands of tokens
    recommended: bool = False
    description: str = ""
