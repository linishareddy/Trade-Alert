"""
client.py

Thin async HTTP client that POSTs raw alerts to the FastAPI ingest endpoint.
"""
from __future__ import annotations
import httpx
from config.settings import settings


async def post_alert(payload: dict) -> bool:
    """
    POST a raw alert dict to the ingest endpoint.
    Returns True on success, False on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.INGEST_URL, json=payload)
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"[DiscordAgent] Failed to post alert: {e}")
        return False
