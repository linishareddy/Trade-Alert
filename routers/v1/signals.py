from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.v1.signals import SignalOut, SignalListOut
from controllers.v1.signals.signal_controller import list_signals, get_signal

router = APIRouter(tags=["signals"])


@router.get("/signals", response_model=SignalListOut)
async def get_signals(
    ticker: str | None = Query(None, description="Filter by ticker symbol"),
    status: str | None = Query(None, description="Filter by status: OPEN, PARTIAL, CLOSED"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SignalListOut:
    """List all parsed trading signals."""
    return await list_signals(db, ticker=ticker, status=status, limit=limit, offset=offset)


@router.get("/signals/{signal_id}", response_model=SignalOut)
async def get_signal_by_id(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
) -> SignalOut:
    """Get a single signal by ID."""
    signal = await get_signal(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal
