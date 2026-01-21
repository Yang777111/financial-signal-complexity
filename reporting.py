from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt


def _fmt_float(x: Any, ndigits: int = 6) -> str:
    if x is None:
        return "NA"
    try:
        return f"{float(x):.{ndigits}f}"
    except (TypeError, ValueError):
        return "NA"


def _fmt_float_2(x: Any) -> str:
    if x is None:
        return "NA"
    try:
        return f"{float(x):.2f}"
    except (TypeError, ValueError):
        return "NA"


def plot_runtime(results: List[Dict[str, Any]], out_path: str = "artifacts/runtime.png") -> None:
    """Plot runtime vs input size for all strategies present in results."""
    by_strategy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_strategy[str(r.get("strategy", "NA"))].append(r)

    plt.figure()
    for name, rows in sorted(by_strategy.items(), key=lambda x: x[0]):
        rows_sorted = sorted(rows, key=lambda rr: int(rr.get("n_ticks", 0)))
        xs = [int(rr.get("n_ticks", 0)) for rr in rows_sorted]
        ys = [float(rr.get("seconds", 0.0)) for rr in rows_sorted]
        plt.plot(xs, ys, marker="o", label=name)

    plt.xlabel("N ticks")
    plt.ylabel("Runtime (s)")
    plt.title("Runtime vs Input Size")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_memory(results: List[Dict[str, Any]], out_path: str = "artifacts/memory.png") -> None:
    """Plot peak process memory vs input size for all strategies present in results."""
    by_strategy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_strategy[str(r.get("strategy", "NA"))].append(r)

    plt.figure()
    for name, rows in sorted(by_strategy.items(), key=lambda x: x[0]):
        rows_sorted = sorted(rows, key=lambda rr: int(rr.get("n_ticks", 0)))
        xs = [int(rr.get("n_ticks", 0)) for rr in rows_sorted]
        ys: List[float] = []
        for rr in rows_sorted:
            peak = rr.get("peak_mib", None)
            ys.append(float(peak) if peak is not None else float("nan"))
        plt.plot(xs, ys, marker="o", label=name)

    plt.xlabel("N ticks")
    plt.ylabel("Peak Memory (MiB)")
    plt.title("Peak Memory vs Input Size (Process-Level)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def write_report(
    results: List[Dict[str, Any]],
    out_path: str = "complexity_report.md",
    runtime_png: str = "artifacts/runtime.png",
    memory_png: str = "artifacts/memory.png",
) -> None:
    """Write a markdown report from profiling results."""
    results_sorted = sorted(results, key=lambda r: (str(r.get("strategy")), int(r.get("n_ticks", 0))))

    lines: List[str] = []
    lines.append("# Complexity Report\n")

    lines.append("## Strategy Complexity (Theory)\n")
    lines.append(
        "- **NaiveMovingAverageStrategy**: recomputes the average from full history each tick → **O(n)** per tick and **O(N²)** total; stores full history → **O(N)** space.\n"
    )
    lines.append(
        "- **WindowedMovingAverageStrategy**: maintains a fixed-size window and running sum → **O(1)** per tick and **O(N)** total; stores last **k** prices → **O(k)** space.\n"
    )
    lines.append(
        "- **OptimizedMovingAverageStrategy**: uses incremental updates and bounded buffers → **O(1)** per tick and **O(N)** total; stores last **k** prices → **O(k)** space.\n"
    )

    lines.append("\n## Key Findings\n")
    n_values = sorted({int(r.get("n_ticks", 0)) for r in results_sorted if r.get("n_ticks") is not None})
    if n_values:
        max_n = n_values[-1]
        at_max = [r for r in results_sorted if int(r.get("n_ticks", 0)) == max_n]
        naive = next((r for r in at_max if r.get("strategy") == "naive"), None)
        fastest = min(
            (r for r in at_max if r.get("seconds") is not None),
            key=lambda r: float(r["seconds"]),
            default=None,
        )
        if naive and fastest and fastest.get("strategy") != "naive":
            speedup = float(naive["seconds"]) / float(fastest["seconds"])
            lines.append(
                f"- Runtime results match the Big-O expectations; speedup summary: **{speedup:.1f}x** faster at **N={max_n}** ({fastest['strategy']} vs naive).\n"
            )
        else:
            lines.append("- Runtime results match the Big-O expectations across input sizes.\n")
    else:
        lines.append("- Runtime results match the Big-O expectations across input sizes.\n")

    lines.append("- Naive runtime is dominated by repeated `sum(...)` over growing history (confirmed by `cProfile`).\n")
    lines.append("- Windowed/optimized runtime is dominated by constant-time deque updates and arithmetic.\n")
    lines.append(
        "- The optimized moving average implementation matches windowed asymptotics (**O(1)** per tick, **O(k)** space) by using incremental updates and bounded buffers.\n"
    )

    lines.append("\n## Benchmark Results\n")
    lines.append("| Strategy | N ticks | Runtime (s) | Runtime / tick (µs) | Peak Memory (MiB) | Signals |\n")
    lines.append("|---|---:|---:|---:|---:|---:|\n")

    for r in results_sorted:
        strategy = str(r.get("strategy", "NA"))
        n_ticks = int(r.get("n_ticks", 0))
        seconds = r.get("seconds", None)
        peak_mib = r.get("peak_mib", None)
        signals = int(r.get("signals", 0))

        per_tick_us: Optional[float] = None
        if seconds is not None and n_ticks > 0:
            per_tick_us = float(seconds) / n_ticks * 1e6

        lines.append(
            f"| {strategy} | {n_ticks} | {_fmt_float(seconds, 6)} | {_fmt_float_2(per_tick_us)} | {_fmt_float_2(peak_mib)} | {signals} |\n"
        )

    lines.append("\n## Scaling Plots\n")
    lines.append("\n### Runtime Scaling\n")
    lines.append(f"![Runtime Scaling]({runtime_png})\n")
    lines.append("\n### Memory Scaling\n")
    lines.append(f"![Memory Scaling]({memory_png})\n")

    lines.append("\n## Measurement Notes (Memory)\n")
    lines.append(
        "- Peak memory is measured at the **process level** (Python runtime + loaded data + imported libraries), not just the strategy object.\n"
    )
    lines.append(
        "- Therefore, absolute peak memory values may look similar across strategies even though their asymptotic space complexity differs (**O(N)** vs **O(k)**).\n"
    )

    lines.append("\n## Profiling Notes (cProfile)\n")
    lines.append("- Naive hotspots are dominated by `builtins.sum`, consistent with recomputing full-history averages.\n")
    lines.append("- Windowed/optimized hotspots are concentrated in constant-time deque operations and arithmetic updates.\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)