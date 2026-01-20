import time

from data_loader import load_market_data
from strategies import WindowedMovingAverageStrategy, OptimizedMovingAverageStrategy


def test_strategies_run_and_return_list():
    ticks = load_market_data("btc_eth_market_data.csv")[:1000]
    s1 = WindowedMovingAverageStrategy(window_size=10)
    s2 = OptimizedMovingAverageStrategy(window_size=10)

    out1 = []
    out2 = []
    for t in ticks:
        out1.append(s1.generate_signals(t))
        out2.append(s2.generate_signals(t))

    assert all(isinstance(x, list) for x in out1)
    assert all(isinstance(x, list) for x in out2)


def test_optimized_under_one_second_for_100k():
    ticks = load_market_data("btc_eth_market_data.csv")[:100_000]
    strat = OptimizedMovingAverageStrategy(window_size=10)

    start = time.perf_counter()
    for t in ticks:
        strat.generate_signals(t)
    end = time.perf_counter()

    elapsed = end - start
    assert elapsed < 1.0, f"Optimized strategy took {elapsed:.3f}s (> 1.0s)"


def test_optimized_window_is_bounded():
    ticks = load_market_data("btc_eth_market_data.csv")[:50_000]
    k = 10
    strat = OptimizedMovingAverageStrategy(window_size=k)

    for t in ticks:
        strat.generate_signals(t)

    for buf in strat._buffers.values():
        assert len(buf) <= k


def run_all_tests():
    tests = [
        ("test_strategies_run_and_return_list", test_strategies_run_and_return_list),
        ("test_optimized_under_one_second_for_100k", test_optimized_under_one_second_for_100k),
        ("test_optimized_window_is_bounded", test_optimized_window_is_bounded),
    ]

    print("Running tests.py ...")
    passed = 0
    for name, fn in tests:
        start = time.perf_counter()
        fn()
        end = time.perf_counter()
        print(f"[PASS] {name} ({(end - start):.3f}s)")
        passed += 1

    print(f"All tests passed: {passed}/{len(tests)}")


if __name__ == "__main__":
    run_all_tests()