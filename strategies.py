from __future__ import annotations

from collections import deque
from typing import Dict, List

from models import MarketDataPoint, Signal, Strategy


class NaiveMovingAverageStrategy(Strategy):
    def __init__(self) -> None:
        self._price_history: Dict[str, List[float]] = {}

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        prices = self._price_history.setdefault(tick.symbol, [])
        prices.append(tick.price)  # O(1) amortized

        # Recompute average from scratch: O(n)
        avg_price = sum(prices) / len(prices)

        if tick.price > avg_price:
            side = "BUY"
        elif tick.price < avg_price:
            side = "SELL"
        else:
            return []

        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                side=side,
                price=tick.price,
                meta={"average": avg_price},
            )
        ]


class WindowedMovingAverageStrategy(Strategy):
    def __init__(self, window_size: int = 10) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")

        self.window_size = window_size
        self._buffers: Dict[str, deque[float]] = {}
        self._running_sum: Dict[str, float] = {}

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        buffer = self._buffers.setdefault(tick.symbol, deque())
        current_sum = self._running_sum.get(tick.symbol, 0.0)

        buffer.append(tick.price)          # O(1)
        current_sum += tick.price          # O(1)

        if len(buffer) > self.window_size:
            removed = buffer.popleft()     # O(1)
            current_sum -= removed         # O(1)

        self._running_sum[tick.symbol] = current_sum

        avg_price = current_sum / len(buffer)  # O(1)

        if tick.price > avg_price:
            side = "BUY"
        elif tick.price < avg_price:
            side = "SELL"
        else:
            return []

        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                side=side,
                price=tick.price,
                meta={"average": avg_price, "window": self.window_size},
            )
        ]


class OptimizedMovingAverageStrategy(Strategy):
    """
    Fixed-window moving average with O(1) per-tick update.
    Space is O(k) per symbol (k = window_size).
    """

    def __init__(self, window_size: int = 10):
        self._window_size = window_size
        self._buffers = {}       # symbol -> deque[float]
        self._running_sums = {}  # symbol -> float
        self._last_signal = {}   # symbol -> str

    def generate_signals(self, tick: MarketDataPoint) -> list:
        sym = tick.symbol
        buf = self._buffers.setdefault(sym, deque())
        s = self._running_sums.get(sym, 0.0)

        buf.append(tick.price)
        s += tick.price

        if len(buf) > self._window_size:
            s -= buf.popleft()

        self._running_sums[sym] = s
        avg = s / len(buf)

        signal = "BUY" if tick.price > avg else "SELL"
        last = self._last_signal.get(sym)

        if signal != last:
            self._last_signal[sym] = signal
            return [signal]
        return []