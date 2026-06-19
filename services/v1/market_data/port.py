"""
MarketDataPort — abstract interface for all price-data providers.

Change MARKET_DATA_PROVIDER in .env to swap without code changes.
Adding a new provider: implement MarketDataPort, add one case to factory.py.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from .models import OHLCVBar


class MarketDataPort(ABC):

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """Return the latest traded price for symbol."""
        ...

    @abstractmethod
    async def get_intraday_bars(
        self,
        symbol: str,
        bar_minutes: int = 1,
        lookback_bars: int = 50,
    ) -> list[OHLCVBar]:
        """
        Return the last `lookback_bars` bars at `bar_minutes` resolution.
        Used for EMA and VWAP computation.
        """
        ...
