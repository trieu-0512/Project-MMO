"""Simple placeholder screener module.

The original project references a richer implementation that
ranks symbols by a blended risk/reward score.  For now we expose a
minimal CLI helper that can be extended with additional metrics.
"""

from __future__ import annotations

import argparse
from typing import List


DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "TRXUSDT",
    "UNIUSDT",
    "LTCUSDT",
    "ATOMUSDT",
]


def run(limit: int) -> List[str]:
    symbols = DEFAULT_SYMBOLS[:limit]
    print("Top symbols (static placeholder):")
    for idx, sym in enumerate(symbols, start=1):
        print(f"{idx:>2}: {sym}")
    return symbols


def main() -> None:
    parser = argparse.ArgumentParser(description="Print placeholder screener results")
    parser.add_argument("--limit", type=int, default=15, help="Number of symbols to show")
    args = parser.parse_args()
    run(args.limit)


if __name__ == "__main__":
    main()
