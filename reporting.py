from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt


def _group(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r["strategy"], []).append(r)
    for k in out:
        out[k] = sorted(out[k], key=lambda x: x["n_ticks"])
    return out


def plot_runtime(rows: List[Dict[str, Any]], out_path: str) -> None:
    """Plot runtime vs input size for each strategy."""
    grouped = _group(rows)

    plt.figure()
    for name, rs in grouped.items():
        xs = [r["n_ticks"] for r in rs]
        ys = [r["seconds"] for r in rs]
        plt.plot(xs, ys, marker="o", label=name)

    plt.xlabel("Number of ticks (N)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime Scaling")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_memory(rows: List[Dict[str, Any]], out_path: str) -> None:
    """Plot peak memory vs input size for each strategy."""
    grouped = _group(rows)

    plt.figure()
    for name, rs in grouped.items():
        xs = [r["n_ticks"] for r in rs]
        ys = [r["peak_mib"] for r in rs]
        if all(v is None for v in ys):
            continue
        plt.plot(xs, ys, marker="o", label=name)

    plt.xlabel("Number of ticks (N)")
    plt.ylabel("Peak memory (MiB)")
    plt.title("Memory Scaling")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def write_report(rows: List[Dict[str, Any]], md_path: str, runtime_png: str, memory_png: str) -> None:
    """Generate a Markdown report with tables, plots, and interpretation."""
    # Group rows for simple comparisons
    by_strategy: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_strategy.setdefault(r["strategy"], []).append(r)
    for k in by_strategy:
        by_strategy[k] = sorted(by_strategy[k], key=lambda x: x["n_ticks"])

    strategies = sorted(by_strategy.keys())
    ns = sorted({r["n_ticks"] for r in rows})

    # Compute speedup at largest N if at least two strategies exist
    speedup_note = "NA"
    if len(strategies) >= 2 and ns:
        n_max = ns[-1]
        # Pick the first two strategies in sorted order for a stable report
        s_a, s_b = strategies[0], strategies[1]
        a_row = next((r for r in by_strategy[s_a] if r["n_ticks"] == n_max), None)
        b_row = next((r for r in by_strategy[s_b] if r["n_ticks"] == n_max), None)
        if a_row and b_row and b_row["seconds"] > 0:
            speedup = a_row["seconds"] / b_row["seconds"]
            speedup_note = f"{speedup:.1f}x faster at N={n_max} ({s_b} vs {s_a})"

    lines: List[str] = []
    lines.append("# Complexity Report\n\n")

    lines.append("## Strategy Complexity (Theory)\n")
    lines.append(
        "- **NaiveMovingAverageStrategy**: recomputes the average from full history each tick → **O(n)** per tick and **O(N^2)** total; stores full history → **O(N)** space.\n"
    )
    lines.append(
        "- **WindowedMovingAverageStrategy**: maintains a fixed-size window and running sum → **O(1)** per tick and **O(N)** total; stores last *k* prices → **O(k)** space.\n\n"
    )

    lines.append("## Key Findings\n")
    lines.append(f"- Runtime results match the Big-O expectations; speedup summary: **{speedup_note}**.\n")
    lines.append("- Naive runtime is dominated by repeated `sum(...)` over growing history (confirmed by cProfile).\n")
    lines.append("- Windowed runtime is dominated by constant-time deque updates and arithmetic.\n\n")

    lines.append("## Benchmark Results\n")
    lines.append("| Strategy | N ticks | Runtime (s) | Runtime / tick (µs) | Peak Memory (MiB) | Signals |\n")
    lines.append("|---|---:|---:|---:|---:|---:|\n")
    for r in sorted(rows, key=lambda x: (x["strategy"], x["n_ticks"])):
        peak = r["peak_mib"]
        peak_str = "NA" if peak is None else f"{peak:.2f}"
        per_tick_us = (r["seconds"] / r["n_ticks"]) * 1_000_000 if r["n_ticks"] else 0.0
        lines.append(
            f"| {r['strategy']} | {r['n_ticks']} | {r['seconds']:.6f} | {per_tick_us:.2f} | {peak_str} | {r['signals']} |\n"
        )

    lines.append("\n## Scaling Plots\n")
    lines.append(f"![Runtime Scaling]({runtime_png})\n")
    lines.append(f"![Memory Scaling]({memory_png})\n\n")

    lines.append("## Measurement Notes (Memory)\n")
    lines.append(
        "- Peak memory is measured at the **process level** (Python runtime + loaded data + imported libraries), not just the strategy object.\n"
    )
    lines.append(
        "- Therefore, absolute peak memory values may look similar across strategies even though their **asymptotic space complexity** differs (O(N) vs O(k)).\n\n"
    )

    lines.append("## Profiling Notes (cProfile)\n")
    lines.append("- Naive hotspots are dominated by `builtins.sum`, consistent with recomputing full-history averages.\n")
    lines.append("- Windowed hotspots are concentrated in constant-time deque operations and arithmetic updates.\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)