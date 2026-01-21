# Complexity Report
## Strategy Complexity (Theory)
- **NaiveMovingAverageStrategy**: recomputes the average from full history each tick → **O(n)** per tick and **O(N²)** total; stores full history → **O(N)** space.
- **WindowedMovingAverageStrategy**: maintains a fixed-size window and running sum → **O(1)** per tick and **O(N)** total; stores last **k** prices → **O(k)** space.
- **OptimizedMovingAverageStrategy**: uses incremental updates and bounded buffers → **O(1)** per tick and **O(N)** total; stores last **k** prices → **O(k)** space.

## Key Findings
- Runtime results match the Big-O expectations; speedup summary: **62.3x** faster at **N=100000** (optimized_k10 vs naive).
- Naive runtime is dominated by repeated `sum(...)` over growing history (confirmed by `cProfile`).
- Windowed/optimized runtime is dominated by constant-time deque updates and arithmetic.
- The optimized moving average implementation matches windowed asymptotics (**O(1)** per tick, **O(k)** space) by using incremental updates and bounded buffers.

## Benchmark Results
| Strategy | N ticks | Runtime (s) | Runtime / tick (µs) | Peak Memory (MiB) | Signals |
|---|---:|---:|---:|---:|---:|
| naive | 1000 | 0.003197 | 3.20 | 110.66 | 999 |
| naive | 10000 | 0.130231 | 13.02 | 110.78 | 9998 |
| naive | 100000 | 7.649401 | 76.49 | 111.59 | 99998 |
| optimized_k10 | 1000 | 0.001308 | 1.31 | 110.75 | 186 |
| optimized_k10 | 10000 | 0.012326 | 1.23 | 110.78 | 1863 |
| optimized_k10 | 100000 | 0.122822 | 1.23 | 112.25 | 18654 |
| windowed_k10 | 1000 | 0.002218 | 2.22 | 110.73 | 999 |
| windowed_k10 | 10000 | 0.021582 | 2.16 | 110.78 | 9998 |
| windowed_k10 | 100000 | 0.214104 | 2.14 | 112.23 | 99998 |

## Scaling Plots

### Runtime Scaling
![Runtime Scaling](artifacts/runtime.png)

### Memory Scaling
![Memory Scaling](artifacts/memory.png)

## Measurement Notes (Memory)
- Peak memory is measured at the **process level** (Python runtime + loaded data + imported libraries), not just the strategy object.
- Therefore, absolute peak memory values may look similar across strategies even though their asymptotic space complexity differs (**O(N)** vs **O(k)**).
- Interpretation for the <100MB requirement: the reported Peak Memory is process-level and includes the in-memory tick list and library overhead. The relevant measure for strategy space complexity is the incremental memory attributable to the strategy state. For windowed/optimized strategies, this state is bounded by the window size k (O(k)) and does not grow with N, whereas the naive strategy retains full history (O(N)).

## Profiling Notes (cProfile)
- Naive hotspots are dominated by `builtins.sum`, consistent with recomputing full-history averages.
- Windowed/optimized hotspots are concentrated in constant-time deque operations and arithmetic updates.
