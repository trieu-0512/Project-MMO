from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict

import numpy as np
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.data.collector import MarketDataCollector
from app.db.models import Account
from app.db.session import AsyncSessionLocal
from app.execution.executor import OrderRequest, executor
from app.logging.journal import log_event
from app.rl.policy_loader import registry
from app.risk.manager import risk_manager
from app.screener.core import run_screener, serialize_results

settings = get_settings()


async def run_cycle(redis_client: redis.Redis) -> None:
    async with AsyncSessionLocal() as session:
        collector = MarketDataCollector(redis_client, session)
        snapshots = await collector.collect_bulk()
        spot_data = {snap.symbol: snap.candles for key, snap in snapshots.items() if snap.campaign == "SPOT"}
        fut_data = {snap.symbol: snap.candles for key, snap in snapshots.items() if snap.campaign == "FUT"}
        spot_results = run_screener(spot_data, "SPOT")
        fut_results = run_screener(fut_data, "FUT")
        await collector.persist_signals(serialize_results(spot_results), "SPOT")
        await collector.persist_signals(serialize_results(fut_results), "FUT")
        nav = await current_nav(session)
        risk_manager.update_nav("SPOT", nav["spot"], nav["fut"])
        risk_manager.update_nav("FUT", nav["spot"], nav["fut"])
        await process_signals(nav, spot_results, "SPOT")
        await process_signals(nav, fut_results, "FUT")


async def current_nav(session: AsyncSession) -> Dict[str, float]:
    result = await session.execute(select(Account))
    account = result.scalar_one_or_none()
    if account is None:
        return {"total": 100000.0, "spot": 60000.0, "fut": 40000.0}
    return {"total": float(account.nav_total), "spot": float(account.nav_spot), "fut": float(account.nav_fut)}


async def process_signals(nav: Dict[str, float], results, campaign: str) -> None:
    if not results:
        return
    nav_value = nav["spot" if campaign == "SPOT" else "fut"]
    for row in results:
        obs = build_observation(row)
        action = registry.predict(campaign, obs)
        confidence = float(action) if np.isscalar(action) else float(action[0])
        req = OrderRequest(
            symbol=row.symbol,
            side="BUY" if confidence >= 0 else "SELL",
            campaign=campaign,
            price=row.last_price,
            atr=row.atr,
            atr_pct=row.atr_pct,
            confidence=abs(confidence),
            expected_return=row.expected_return,
            fee=settings.fee_taker_spot if campaign == "SPOT" else settings.fee_taker_fut,
            leverage=1.0 if campaign == "SPOT" else 2.0,
        )
        result = executor.execute(nav_value, req)
        if result.accepted:
            risk_manager.register_win(campaign)
            log_event("order_executed", {"campaign": campaign, "symbol": row.symbol, "order": result.order_response})
        else:
            risk_manager.register_loss(campaign)
            log_event("order_rejected", {"campaign": campaign, "symbol": row.symbol, "reason": result.reason})


def build_observation(row) -> np.ndarray:
    return np.array([
        row.expected_return,
        row.atr_pct / 100,
        row.sharpe,
        row.sortino,
        row.rr,
    ], dtype=float)


async def main() -> None:
    redis_client = redis.from_url(settings.redis_url)
    while True:
        log_event("scheduler_tick", {"time": datetime.utcnow().isoformat()})
        await run_cycle(redis_client)
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
