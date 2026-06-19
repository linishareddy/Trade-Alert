"""Broker-agnostic OHLCV bar — used for EMA/VWAP computation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OHLCVBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
