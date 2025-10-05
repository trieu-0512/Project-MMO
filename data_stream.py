from typing import Optional

import pandas as pd
from binance.spot import Spot


class CandleFeed:
    def __init__(self, symbol: str, interval: str = "1m", limit: int = 200, client: Optional[Spot] = None):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.client = client or Spot()

    def fetch(self) -> pd.DataFrame:
        raw = self.client.klines(self.symbol, self.interval, limit=self.limit)
        cols = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "trades",
            "tb_base",
            "tb_quote",
            "ignore",
        ]
        df = pd.DataFrame(raw, columns=cols)
        for col in ["open", "high", "low", "close", "volume", "qav", "tb_base", "tb_quote"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
        return df

    def latest_close(self) -> float:
        df = self.fetch()
        return float(df["close"].iloc[-1])
