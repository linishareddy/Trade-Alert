from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.v1.trades import PaperTradeResponse, TradeListResponse, TradeSummaryResponse
from services.v1.trades import trade_service


async def handle_list(
    db: AsyncSession,
    symbol: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> TradeListResponse:
    total, trades = await trade_service.list_trades(db, symbol, status, limit, offset)
    return TradeListResponse(
        total=total,
        trades=[PaperTradeResponse.model_validate(t) for t in trades],
    )


async def handle_get(db: AsyncSession, trade_id: str) -> PaperTradeResponse | None:
    trade = await trade_service.get_trade_by_id(db, trade_id)
    if not trade:
        return None
    return PaperTradeResponse.model_validate(trade)


async def handle_summary(db: AsyncSession) -> TradeSummaryResponse:
    data = await trade_service.get_summary(db)
    return TradeSummaryResponse(**data)
