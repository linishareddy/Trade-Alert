"""
main.py — FastAPI app factory + entry point.

Running `python main.py` starts both:
  - The FastAPI server (via uvicorn)
  - The Discord self-bot agent (via asyncio)
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from config.settings import settings
from db.session import engine, Base
from routers.v1.health import router as health_router
from routers.v1.ingest import router as ingest_router
from routers.v1.signals import router as signals_router


# ── Database init ─────────────────────────────────────────────────────────────

async def init_db(eng: AsyncEngine) -> None:
    """Create all tables if they don't exist (dev convenience — use Alembic in prod)."""
    # Import models so Base knows about them
    import db.models  # noqa: F401
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── App factory ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trade Alert API",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    prefix = settings.API_V1_STR
    app.include_router(health_router, prefix=prefix)
    app.include_router(ingest_router, prefix=prefix)
    app.include_router(signals_router, prefix=prefix)

    return app


app = create_app()


# ── Entry point ───────────────────────────────────────────────────────────────

async def _main() -> None:
    import uvicorn
    from agents.discord.discord_agent import run_discord_agent

    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,       # reload=True is incompatible with asyncio task sharing
        log_level="info",
    )
    server = uvicorn.Server(config)

    # Run FastAPI + Discord agent concurrently
    await asyncio.gather(
        server.serve(),
        run_discord_agent(),
    )


if __name__ == "__main__":
    asyncio.run(_main())
