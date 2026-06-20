"""
client.py

Delivers raw Discord alerts into the ingest pipeline in-process.
Avoids HTTP loopback to localhost, which can deadlock/time out when
Discord and FastAPI share the same asyncio event loop.
"""
from __future__ import annotations

from db.session import AsyncSessionLocal
from schemas.v1.ingest import RawAlertIn
from services.v1.discord import ingestion_service


async def post_alert(payload: dict) -> bool:
    """
    Deliver a raw alert dict to the ingest pipeline.
    Returns True on success, False on failure.
    """
    try:
        alert = RawAlertIn(**payload)
        async with AsyncSessionLocal() as db:
            accepted, _ = await ingestion_service.ingest_alert(db, alert)
        return accepted
    except Exception as exc:
        print(f"[DiscordAgent] Failed to post alert: {type(exc).__name__}: {exc!r}")
        return False
