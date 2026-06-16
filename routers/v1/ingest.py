from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.v1.ingest import RawAlertIn, IngestResponse
from controllers.v1.ingest.ingest_controller import handle_alert

router = APIRouter(tags=["ingest"])


@router.post("/ingest/alert", response_model=IngestResponse)
async def ingest_alert(
    alert: RawAlertIn,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Receive a raw Discord alert from the self-bot agent."""
    return await handle_alert(db, alert)
