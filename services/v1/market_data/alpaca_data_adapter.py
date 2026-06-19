"""
AlpacaData — real-time market data via Alpaca Markets (free plan included).

Used when MARKET_DATA_PROVIDER=alpaca.
Requires the same ALPACA_API_KEY / ALPACA_API_SECRET as the broker.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from .port import MarketDataPort
from .models import OHLCVBar

logger = logging.getLogger(__name__)


class AlpacaData(MarketDataPort):

    def __init__(self, api_key: str, api_secret: str) -> None:
        from alpaca.data.historical import StockHistoricalDataClient
        self._client = StockHistoricalDataClient(api_key, api_secret)

    async def get_current_price(self, symbol: str) -> float:
        from alpaca.data.requests import StockLatestTradeRequest
        req = StockLatestTradeRequest(symbol_or_symbols=symbol)
        trades = await asyncio.to_thread(self._client.get_stock_latest_trade, req)
        price = float(trades[symbol].price)
        logger.debug("[AlpacaData] %s current price = %.4f", symbol, price)
        return price

    async def get_intraday_bars(
        self,
        symbol: str,
        bar_minutes: int = 1,
        lookback_bars: int = 50,
    ) -> list[OHLCVBar]:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        end = datetime.now(timezone.utc)
        # Fetch enough history to cover lookback_bars plus some buffer
        start = end - timedelta(hours=4)

        tf = TimeFrame(bar_minutes, TimeFrameUnit.Minute)
        req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=tf, start=start, end=end)
        bars_resp = await asyncio.to_thread(self._client.get_stock_bars, req)

        bars: list[OHLCVBar] = []
        for b in bars_resp[symbol]:
            bars.append(OHLCVBar(
                timestamp=b.timestamp,
                open=float(b.open),
                high=float(b.high),
                low=float(b.low),
                close=float(b.close),
                volume=float(b.volume),
            ))

        result = bars[-lookback_bars:]
        logger.debug("[AlpacaData] %s returned %d bars", symbol, len(result))
        return result
