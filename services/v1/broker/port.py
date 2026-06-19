"""
BrokerPort — the abstract interface every broker adapter must implement.

The execution agent and monitor agent import ONLY this interface.
Broker-specific code lives exclusively in the adapter files
(alpaca_broker.py, webull_broker.py, etc.).

To add a new broker:
  1. Create services/v1/broker/<name>_broker.py implementing BrokerPort
  2. Add one case to services/v1/broker/factory.py
  3. Set BROKER=<name> in .env
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from .models import BracketOrderRequest, BrokerOrderResult, Position


class BrokerPort(ABC):

    @abstractmethod
    async def place_bracket_order(
        self, request: BracketOrderRequest
    ) -> BrokerOrderResult:
        """
        Open a position with automatic take-profit and stop-loss attached.
        Brokers that don't support native bracket orders must simulate them.
        """
        ...

    @abstractmethod
    async def get_open_positions(self) -> list[Position]:
        """Return all currently open positions for this account."""
        ...

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> str:
        """Return the current status string for a given order ID."""
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel a pending order. Returns True if successfully cancelled."""
        ...
