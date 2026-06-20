from __future__ import annotations

import ssl

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings


def _build_connect_args() -> dict:
    if not settings.DB_SSL:
        return {}
    if settings.DB_SSL_CA_FILE:
        ctx = ssl.create_default_context(cafile=settings.DB_SSL_CA_FILE)
    else:
        # Aiven-managed Postgres; skip CA verify when no ca.pem path is configured
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=_build_connect_args(),
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
