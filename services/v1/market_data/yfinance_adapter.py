"""
YFinanceData — market data adapter using yfinance (free, no API key needed).

Note: yfinance data can be 15 min delayed for some symbols during market hours.
Suitable for paper trading validation. Switch to MARKET_DATA_PROVIDER=alpaca
for real-time data once you have an Alpaca key.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import timezone

import yfinance as yf

from .port import MarketDataPort
from .models import OHLCVBar

logger = logging.getLogger(__name__)


class YFinanceData(MarketDataPort):

    async def get_current_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)
        info = await asyncio.to_thread(lambda: ticker.fast_info)
        price = float(info.last_price)
        logger.debug("[YFinanceData] %s current price = %.4f", symbol, price)
        return price

    async def get_intraday_bars(
        self,
        symbol: str,
        bar_minutes: int = 1,
        lookback_bars: int = 50,
    ) -> list[OHLCVBar]:
        ticker = yf.Ticker(symbol)
        interval = f"{bar_minutes}m"

        df = await asyncio.to_thread(
            ticker.history,
            period="1d",
            interval=interval,
            auto_adjust=True,
        )

        if df is None or df.empty:
            logger.warning("[YFinanceData] No bars returned for %s interval=%s", symbol, interval)
            return []

        bars: list[OHLCVBar] = []
        for ts, row in df.iterrows():
            # pandas Timestamp → aware datetime
            dt = ts.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            bars.append(OHLCVBar(
                timestamp=dt,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            ))

        result = bars[-lookback_bars:]
        logger.debug("[YFinanceData] %s returned %d bars", symbol, len(result))
        return result
