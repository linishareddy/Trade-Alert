from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.session import get_db
from schemas.v1.health import (
    HealthResponse, ConfigResponse,
    ConfigUpdateRequest, ConfigUpdateResponse,
    ConfigResetResponse, GroqModel,
)
from config.settings import settings
from services.v1.auth.dependencies import get_current_user
from services.v1.config.runtime_settings import runtime, EDITABLE

router = APIRouter()

# ── Curated Groq model list ───────────────────────────────────────────────────
# Update this list when Groq adds new models worth exposing.

_GROQ_MODELS: list[dict] = [
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B",
        "speed": "medium",
        "context_k": 128,
        "recommended": True,
        "description": "Best accuracy for complex signal parsing",
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B",
        "speed": "fast",
        "context_k": 128,
        "recommended": False,
        "description": "Fastest — great for simple well-structured formats",
    },
    {
        "id": "llama3-70b-8192",
        "name": "Llama 3 70B",
        "speed": "medium",
        "context_k": 8,
        "recommended": False,
        "description": "Classic Llama 3, 8k context window",
    },
    {
        "id": "mixtral-8x7b-32768",
        "name": "Mixtral 8x7B",
        "speed": "medium",
        "context_k": 32,
        "recommended": False,
        "description": "Strong reasoning, 32k context",
    },
    {
        "id": "gemma2-9b-it",
        "name": "Gemma 2 9B",
        "speed": "fast",
        "context_k": 8,
        "recommended": False,
        "description": "Google model — efficient and accurate",
    },
    {
        "id": "deepseek-r1-distill-llama-70b",
        "name": "DeepSeek R1 70B",
        "speed": "slow",
        "context_k": 128,
        "recommended": False,
        "description": "Advanced chain-of-thought reasoning",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_config() -> ConfigResponse:
    """Build ConfigResponse using runtime values (DB overrides win over .env)."""
    return ConfigResponse(
        broker=settings.BROKER,
        alpaca_paper=settings.ALPACA_PAPER,
        execution_enabled=runtime.get("execution_enabled"),
        ema_vwap_enabled=runtime.get("ema_vwap_enabled"),
        market_hours_only=runtime.get("market_hours_only"),
        market_open=settings.MARKET_OPEN,
        market_close=settings.MARKET_CLOSE,
        take_profit_pct=runtime.get("take_profit_pct"),
        stop_loss_pct=runtime.get("stop_loss_pct"),
        default_qty=runtime.get("default_qty"),
        market_data_provider=settings.MARKET_DATA_PROVIDER,
        ema_periods=settings.EMA_PERIODS,
        bar_lookback=settings.BAR_LOOKBACK,
        bar_minutes=settings.BAR_MINUTES,
        supported_contracts=settings.SUPPORTED_CONTRACTS,
        ai_parsing_enabled=runtime.get("ai_parsing_enabled"),
        ai_model=runtime.get("ai_model"),
        whatsapp_enabled=runtime.get("whatsapp_enabled"),
        db_host=settings.DB_HOST,
        db_port=settings.DB_PORT,
        db_name=settings.DB_NAME,
        environment=settings.ENVIRONMENT,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def check_health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.ENVIRONMENT)


@router.get("/config", response_model=ConfigResponse)
def get_config(_: User = Depends(get_current_user)) -> ConfigResponse:
    """Live runtime configuration — reflects DB overrides instantly."""
    return _build_config()


@router.patch("/config", response_model=ConfigUpdateResponse)
async def update_config(
    req: ConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConfigUpdateResponse:
    """Update a single runtime config value. Persists to DB immediately."""
    if req.key not in EDITABLE:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.key}' is read-only. Editable keys: {list(EDITABLE)}",
        )
    try:
        await runtime.set(req.key, req.value, db)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ConfigUpdateResponse(
        key=req.key,
        value=runtime.get(req.key),
        config=_build_config(),
    )


@router.delete("/config/{key}", response_model=ConfigResetResponse)
async def reset_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ConfigResetResponse:
    """Remove DB override for a key — value reverts to .env default."""
    if key not in EDITABLE:
        raise HTTPException(
            status_code=400,
            detail=f"'{key}' is not a runtime-editable key",
        )
    await runtime.reset(key, db)
    return ConfigResetResponse(key=key, config=_build_config())


@router.get("/config/models", response_model=list[GroqModel])
def get_models(_: User = Depends(get_current_user)) -> list[GroqModel]:
    """Returns the curated list of available Groq models for AI parsing."""
    return [GroqModel(**m) for m in _GROQ_MODELS]
