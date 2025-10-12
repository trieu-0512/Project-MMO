from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd
import redis.asyncio as redis
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Alert, Signal
from app.exchange.binance_fut import BinanceFuturesGateway
from app.exchange.binance_spot import BinanceSpotGateway

settings = get_settings()


@dataclass
class MarketSnapshot:
    symbol: str
    campaign: str
    interval: str
    candles: pd.DataFrame
    funding: float | None = None


def klines_to_df(klines: List[List[str]]) -> pd.DataFrame:
    df = pd.DataFrame(
        klines,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trade_count",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume", "trade_count"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    df.set_index("open_time", inplace=True)
    return df


class MarketDataCollector:
    def __init__(self, redis_client: redis.Redis, session: AsyncSession) -> None:
        self.redis = redis_client
        self.session = session
        self.spot = BinanceSpotGateway()
        self.fut = BinanceFuturesGateway()

    async def collect_symbol(self, symbol: str, campaign: str) -> MarketSnapshot:
        is_futures = campaign == "FUT"
        gateway = self.fut if is_futures else self.spot
        klines = await asyncio.to_thread(gateway.klines, symbol=symbol, interval=settings.interval, limit=500)
        df = klines_to_df(klines)
        funding = None
        if is_futures:
            funding_data = await asyncio.to_thread(self.fut.funding_rate, symbol=symbol)
            if funding_data:
                funding = float(funding_data.get("fundingRate", 0))
        cache_key = f"md:{campaign.lower()}:{symbol}:{settings.interval}"
        await self.redis.set(cache_key, df.tail(1).to_json())
        return MarketSnapshot(symbol=symbol, campaign=campaign, interval=settings.interval, candles=df, funding=funding)

    async def collect_bulk(self) -> Dict[str, MarketSnapshot]:
        tasks = []
        for symbol in settings.spot_symbols:
            tasks.append(self.collect_symbol(symbol, "SPOT"))
        for symbol in settings.fut_symbols:
            tasks.append(self.collect_symbol(symbol, "FUT"))
        snapshots = await asyncio.gather(*tasks)
        return {f"{snap.campaign}:{snap.symbol}": snap for snap in snapshots}

    async def persist_signals(self, screener_rows: Iterable[Dict[str, float]], campaign: str) -> None:
        rows = [
            {
                "campaign": campaign,
                "symbol": row["symbol"],
                "score": row["score"],
                "atr_pct": row["atr_pct"],
                "exp_ret": row["expected_return"],
                "action": row["action"],
                "meta": {
                    "sortino": row.get("sortino"),
                    "sharpe": row.get("sharpe"),
                    "atr": row.get("atr"),
                    "last_price": row.get("last_price"),
                },
            }
            for row in screener_rows
        ]
        if not rows:
            return
        await self.session.execute(insert(Signal).values(rows))
        await self.session.commit()

    async def emit_alert(self, message: str, severity: str = "INFO", context: Dict[str, float] | None = None) -> None:
        await self.session.execute(
            insert(Alert).values(
                {
                    "severity": severity,
                    "message": message,
                    "context": context or {},
                }
            )
        )
        await self.session.commit()
