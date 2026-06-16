"""
ingest_controller.py

Orchestrates the ingest use case — accepts a raw alert and returns
the ingestion result. Translates between schemas and services.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.v1.ingest import RawAlertIn, IngestResponse
from services.v1.discord import ingestion_service


async def handle_alert(db: AsyncSession, alert: RawAlertIn) -> IngestResponse:
    accepted, signal = await ingestion_service.ingest_alert(db, alert)

    return IngestResponse(
        accepted=accepted,
        signal_id=signal.id if signal else None,
        action=signal.action.value if signal else None,
    )
