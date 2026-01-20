from __future__ import annotations

import os

from typing import Iterable, List, Tuple

from data_loader import load_market_data
from models import MarketDataPoint, Strategy


def run_strategy(strategy: Strategy, ticks: Iterable[MarketDataPoint]) -> int:
    """Run a strategy over ticks and return total number of emitted signals."""
    total_signals = 0
    for tick in ticks:
        signals = strategy.generate_signals(tick)
        total_signals += len(signals)
    return total_signals


def make_slices(ticks: List[MarketDataPoint], sizes: List[int]) -> List[Tuple[int, List[MarketDataPoint]]]:
    """Return (n, ticks[:n]) pairs for each n in sizes."""
    out: List[Tuple[int, List[MarketDataPoint]]] = []
    for n in sizes:
        out.append((n, ticks[: min(n, len(ticks))]))
    return out


def main() -> None:
    csv_path = "btc_eth_market_data.csv"
    ticks = load_market_data(csv_path)

    sizes = [1_000, 10_000, 100_000]
    slices = make_slices(ticks, sizes)

    from strategies import NaiveMovingAverageStrategy, WindowedMovingAverageStrategy, OptimizedMovingAverageStrategy
    from profiler import profile_runtime_memory
    from reporting import plot_runtime, plot_memory, write_report

    strategy_factories = [
        ("naive", lambda: NaiveMovingAverageStrategy()),
        ("windowed_k10", lambda: WindowedMovingAverageStrategy(window_size=10)),
        ("optimized_k10", lambda: OptimizedMovingAverageStrategy(window_size=10)),
    ]

    # results is created HERE
    results = profile_runtime_memory(
        strategy_factories=strategy_factories,
        slices=slices,
        runner=run_strategy,
        do_cprofile=True,
        do_memory=True,
    )

    # results is used ONLY AFTER it exists
    os.makedirs("artifacts", exist_ok=True)
    runtime_png = "artifacts/runtime.png"
    memory_png = "artifacts/memory.png"
    report_md = "complexity_report.md"

    plot_runtime(results, runtime_png)
    plot_memory(results, memory_png)
    write_report(results, report_md, runtime_png, memory_png)

    for row in results:
        print(row)


if __name__ == "__main__":
    main()