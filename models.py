from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class MarketDataPoint:
    """
    Immutable market tick.

    Space complexity:
    - One object stores O(1) fields.
    - Storing n ticks in a list requires O(n) space (plus Python object overhead).
    """
    timestamp: datetime
    symbol: str
    price: float


@dataclass(frozen=True)
class Signal:
    """
    Minimal signal emitted by a strategy.
    """
    timestamp: datetime
    symbol: str
    side: str  # "BUY" or "SELL"
    price: float
    meta: Optional[Dict[str, Any]] = None


class Strategy(ABC):
    """
    Strategy interface: process one tick and optionally emit signals.
    """
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        raise NotImplementedError