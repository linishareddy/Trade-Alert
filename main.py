"""
main.py — FastAPI app factory + entry point.

Running `python main.py` starts three concurrent tasks:
  1. FastAPI server (via uvicorn)
  2. Discord self-bot agent (watches channels, POSTs alerts)
  3. Position monitor agent (polls open trades, syncs TP/SL exits)
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from config.settings import settings
from db.session import engine, Base
from routers.v1.auth import router as auth_router
from routers.v1.health import router as health_router
from routers.v1.ingest import router as ingest_router
from routers.v1.integrations import router as integrations_router
from routers.v1.signals import router as signals_router
from routers.v1.trades import router as trades_router
from services.v1.auth.dependencies import get_current_user


# ── Database init ─────────────────────────────────────────────────────────────

async def init_db(eng: AsyncEngine) -> None:
    import db.models  # noqa: F401 — registers all models with Base
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── App factory ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    # Load runtime config overrides from DB into memory
    from db.session import AsyncSessionLocal
    from services.v1.config.runtime_settings import runtime
    async with AsyncSessionLocal() as db:
        await runtime.load(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trade Alert API",
        version="2.0.0",
        description=(
            "Discord → Parse → EMA/VWAP validate → Paper trade via broker-agnostic port. "
            f"Active broker: {settings.BROKER.upper()} | "
            f"Market data: {settings.MARKET_DATA_PROVIDER} | "
            f"Execution enabled: {settings.EXECUTION_ENABLED}"
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.API_V1_STR
    protected = [Depends(get_current_user)]

    app.include_router(auth_router,         prefix=prefix)
    app.include_router(health_router,       prefix=prefix)
    app.include_router(ingest_router,       prefix=prefix)
    app.include_router(integrations_router, prefix=prefix, dependencies=protected)
    app.include_router(signals_router,      prefix=prefix, dependencies=protected)
    app.include_router(trades_router,       prefix=prefix, dependencies=protected)

    return app


app = create_app()


# ── Entry point ───────────────────────────────────────────────────────────────

async def _main() -> None:
    import logging
    import uvicorn
    from agents.discord.discord_agent import run_discord_agent
    from agents.monitor.monitor_agent import run_monitor_agent

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
    server = uvicorn.Server(config)

    print(f"[Main] Broker: {settings.BROKER.upper()} | Execution: {settings.EXECUTION_ENABLED}")
    print(f"[Main] TP: +{int(settings.TAKE_PROFIT_PCT*100)}% | SL: -{int(settings.STOP_LOSS_PCT*100)}%")

    await asyncio.gather(
        server.serve(),
        run_discord_agent(),
        run_monitor_agent(),
    )


if __name__ == "__main__":
    asyncio.run(_main())
