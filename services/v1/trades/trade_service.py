"""DB access for PaperTrade records."""
from __future__ import annotations
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.paper_trade import PaperTrade, TradeStatus


async def list_trades(
    db: AsyncSession,
    symbol: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[PaperTrade]]:
    base = select(PaperTrade)
    if symbol:
        base = base.where(PaperTrade.symbol == symbol.upper())
    if status:
        base = base.where(PaperTrade.status == TradeStatus(status))

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(
        base.order_by(PaperTrade.created_at.desc()).limit(limit).offset(offset)
    )).scalars().all()

    return total, list(rows)


async def get_trade_by_id(db: AsyncSession, trade_id: str) -> PaperTrade | None:
    result = await db.execute(select(PaperTrade).where(PaperTrade.id == trade_id))
    return result.scalar_one_or_none()


async def get_summary(db: AsyncSession) -> dict:
    """Return aggregate stats across all closed trades."""
    result = await db.execute(
        select(
            func.count(PaperTrade.id).label("total"),
            func.sum(
                func.cast(PaperTrade.status == TradeStatus.OPEN, func.Integer)
            ).label("open"),
            func.sum(
                func.cast(PaperTrade.status == TradeStatus.CLOSED, func.Integer)
            ).label("closed"),
            func.avg(PaperTrade.pnl_pct).label("avg_pnl_pct"),
            func.sum(PaperTrade.pnl_dollars).label("total_pnl_dollars"),
        )
    )
    row = result.one()
    return {
        "total_trades": row.total or 0,
        "open_trades": row.open or 0,
        "closed_trades": row.closed or 0,
        "avg_pnl_pct": round(float(row.avg_pnl_pct), 2) if row.avg_pnl_pct else None,
        "total_pnl_dollars": round(float(row.total_pnl_dollars), 2) if row.total_pnl_dollars else None,
    }
