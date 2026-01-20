# Runtime & Space Complexity in Financial Signal Processing

## Overview
This project studies how algorithmic design choices affect runtime and memory usage in financial signal processing systems.  
Using historical cryptocurrency market data, we implement multiple moving average–based trading strategies with different time and space complexities, profile their performance, and visualize their scaling behavior.

The focus is on:
- Theoretical Big-O analysis
- Empirical runtime and memory profiling
- Optimization of naive algorithms for scalability

---

## Project Structure
```
PyCharmMiscProject/
├── artifacts/
│   ├── runtime.png
│   └── memory.png
├── btc_eth_market_data.csv
├── complexity_report.md
├── data_loader.py
├── models.py
├── strategies.py
├── profiler.py
├── reporting.py
├── main.py
├── tests.py
└── README.md
```
---

## Data
- Source: Coinbase historical hourly OHLC data
- Assets: BTC and ETH
- Fields used: `timestamp`, `symbol`, `price`

The raw market data was preprocessed into a single CSV file (`btc_eth_market_data.csv`).  
The dataset contains over 170,000 hourly observations, which is sufficient to evaluate performance scaling up to 100,000 ticks.

---

## Strategy Implementations

### NaiveMovingAverageStrategy
- Recomputes the moving average from the full price history at every tick
- Time complexity:
  - Per tick: **O(n)**
  - Total: **O(N²)**
- Space complexity: **O(N)**

### WindowedMovingAverageStrategy
- Maintains a fixed-size sliding window and a running sum
- Time complexity:
  - Per tick: **O(1)**
  - Total: **O(N)**
- Space complexity: **O(k)**, where *k* is the window size

### OptimizedMovingAverageStrategy
- Uses efficient deque operations and incremental updates
- Achieves **O(1)** per-tick time and **O(k)** space
- Designed to scale efficiently to large input sizes

---

## Profiling & Benchmarking
Strategies are benchmarked on input sizes of:
- 1,000 ticks
- 10,000 ticks
- 100,000 ticks

Profiling tools used:
- Wall-clock timing via `time.perf_counter`
- `cProfile` for hotspot analysis
- `memory_profiler` for peak process-level memory usage

Runtime and memory scaling plots are generated and saved under the `artifacts/` directory.  
Detailed benchmark results and interpretations are provided in `complexity_report.md`.

---

## Tests
Basic correctness and performance checks are implemented as a lightweight executable script.

### Run tests
```bash
python tests.py