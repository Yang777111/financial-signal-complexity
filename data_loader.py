from __future__ import annotations

import csv
from datetime import datetime
from typing import List, Optional

from models import MarketDataPoint


def _parse_timestamp(ts: str) -> datetime:
    """
    Parse timestamps in the format:
    - 'YYYY-MM-DD HH:MM:SS'
    - ISO-8601 compatible strings
    """
    ts = ts.strip()

    # Fast path: standard 'YYYY-MM-DD HH:MM:SS'
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # Fallback: ISO-8601 variants
    try:
        return datetime.fromisoformat(ts)
    except ValueError as exc:
        raise ValueError(f"Unrecognized timestamp format: {ts!r}") from exc


def load_market_data(
    csv_path: str = "eth_data_market_data.csv",
    symbol_filter: Optional[str] = None,
) -> List[MarketDataPoint]:
    """
    Load the entire CSV into memory.

    Time:  O(n) rows
    Space: O(n) ticks stored in a list
    """
    ticks: List[MarketDataPoint] = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "symbol", "price"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns: {sorted(required)}; got: {reader.fieldnames}")

        for row in reader:
            symbol = row["symbol"].strip()
            if symbol_filter is not None and symbol != symbol_filter:
                continue

            tick = MarketDataPoint(
                timestamp=_parse_timestamp(row["timestamp"]),
                symbol=symbol,
                price=float(row["price"]),
            )
            ticks.append(tick)

    return ticks