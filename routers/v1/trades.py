from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.v1.trades import PaperTradeResponse, TradeListResponse, TradeSummaryResponse
from controllers.v1.trades.trade_controller import handle_list, handle_get, handle_summary

router = APIRouter(tags=["trades"])


@router.get("/trades", response_model=TradeListResponse)
async def list_trades(
    symbol: str | None = Query(None, description="Filter by ticker symbol"),
    status: str | None = Query(None, description="OPEN | CLOSED | CANCELLED"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> TradeListResponse:
    """List paper trades with optional filtering."""
    return await handle_list(db, symbol, status, limit, offset)


@router.get("/trades/summary", response_model=TradeSummaryResponse)
async def trade_summary(db: AsyncSession = Depends(get_db)) -> TradeSummaryResponse:
    """Aggregate P&L summary across all closed trades."""
    return await handle_summary(db)


@router.get("/trades/{trade_id}", response_model=PaperTradeResponse)
async def get_trade(trade_id: str, db: AsyncSession = Depends(get_db)) -> PaperTradeResponse:
    """Get a single paper trade by ID."""
    trade = await handle_get(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
