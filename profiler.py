from __future__ import annotations

import cProfile
import io
import pstats
import time
from dataclasses import asdict, dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Any

from models import MarketDataPoint, Strategy


Runner = Callable[[Strategy, Iterable[MarketDataPoint]], int]


@dataclass(frozen=True)
class ProfileRow:
    strategy: str
    n_ticks: int
    seconds: float
    signals: int
    peak_mib: Optional[float] = None
    cprofile_top: Optional[str] = None


def _run_with_timer(runner: Runner, strategy: Strategy, ticks: List[MarketDataPoint]) -> Tuple[float, int]:
    start = time.perf_counter()
    signals = runner(strategy, ticks)
    end = time.perf_counter()
    return (end - start), signals


def _run_with_cprofile(runner: Runner, strategy: Strategy, ticks: List[MarketDataPoint], top_k: int = 15) -> Tuple[float, int, str]:
    pr = cProfile.Profile()
    start = time.perf_counter()
    pr.enable()
    signals = runner(strategy, ticks)
    pr.disable()
    end = time.perf_counter()

    s = io.StringIO()
    stats = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("tottime")
    stats.print_stats(top_k)
    return (end - start), signals, s.getvalue()


def _run_with_memory(runner: Runner, strategy: Strategy, ticks: List[MarketDataPoint]) -> Tuple[float, int, Optional[float]]:
    """
    Uses memory_profiler if available.
    Returns peak memory in MiB (approx), else None.
    """
    try:
        from memory_profiler import memory_usage  # type: ignore
    except Exception:
        # memory_profiler is optional; keep the pipeline running without it.
        seconds, signals = _run_with_timer(runner, strategy, ticks)
        return seconds, signals, None

    # memory_usage can call a function and sample process memory.
    def _task() -> int:
        return runner(strategy, ticks)

    start = time.perf_counter()
    mem_series = memory_usage((_task, ()), interval=0.05, timeout=None, max_usage=False, retval=False)
    end = time.perf_counter()

    # Peak in MiB.
    peak = max(mem_series) if mem_series else None
    # Re-run once to get signals deterministically (cheap relative to profiling).
    signals = runner(strategy, ticks)

    return (end - start), signals, peak

def profile_runtime_memory(
    strategy_factories: List[Tuple[str, Callable[[], Strategy]]],
    slices: List[Tuple[int, List[MarketDataPoint]]],
    runner: Runner,
    do_cprofile: bool = True,
    do_memory: bool = True,
) -> List[Dict[str, Any]]:
    """
    Profile runtime and memory for each strategy at each input size.
    Returns list of dict rows (easy to dump to Markdown/CSV later).
    """
    rows: List[ProfileRow] = []

    for n, tick_slice in slices:
        for name, factory in strategy_factories:
            strat_fresh = factory()

            if do_cprofile:
                seconds, signals, top = _run_with_cprofile(runner, strat_fresh, tick_slice)
                row = ProfileRow(strategy=name, n_ticks=n, seconds=seconds, signals=signals, cprofile_top=top)
            else:
                seconds, signals = _run_with_timer(runner, strat_fresh, tick_slice)
                row = ProfileRow(strategy=name, n_ticks=n, seconds=seconds, signals=signals)

            if do_memory:
                strat_mem = factory()
                _, _, peak = _run_with_memory(runner, strat_mem, tick_slice)
                row = ProfileRow(
                    strategy=row.strategy,
                    n_ticks=row.n_ticks,
                    seconds=row.seconds,
                    signals=row.signals,
                    peak_mib=peak,
                    cprofile_top=row.cprofile_top,
                )

            rows.append(row)

    return [asdict(r) for r in rows]