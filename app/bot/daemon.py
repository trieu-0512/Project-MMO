from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.data.collector import MarketDataCollector
from app.db.session import AsyncSessionLocal
from app.logging.journal import log_event
from app.risk.manager import risk_manager

settings = get_settings()


async def heartbeat(redis_client: redis.Redis) -> None:
    while True:
        now = datetime.utcnow()
        await redis_client.set("bot:heartbeat", now.timestamp())
        log_event("heartbeat", {"timestamp": now.isoformat()})
        await asyncio.sleep(30)


async def monitor_positions(session: AsyncSession, redis_client: redis.Redis) -> None:
    collector = MarketDataCollector(redis_client, session)
    while True:
        try:
            snapshots = await collector.collect_bulk()
            await evaluate_trailing(session, snapshots)
        except Exception as exc:  # pragma: no cover - defensive
            log_event("monitor_error", {"error": str(exc)})
        await asyncio.sleep(60)


async def evaluate_trailing(session: AsyncSession, snapshots: Dict[str, Any]) -> None:
    for campaign, state in risk_manager.state.items():
        if state.is_paused():
            log_event("campaign_paused", {"campaign": campaign, "until": state.paused_until.isoformat()})
    # Placeholder: trailing SL logic would inspect open positions and snapshots
    log_event("trailing_check", {"snapshots": list(snapshots.keys())})


async def daily_reset() -> None:
    while True:
        for state in risk_manager.state.values():
            if datetime.utcnow() - state.last_reset > timedelta(hours=24):
                state.losses_streak = 0
                state.last_reset = datetime.utcnow()
                state.paused_until = None
        await asyncio.sleep(3600)


async def main() -> None:
    redis_client = redis.from_url(settings.redis_url)
    async with AsyncSessionLocal() as session:
        await asyncio.gather(
            heartbeat(redis_client),
            monitor_positions(session, redis_client),
            daily_reset(),
        )


if __name__ == "__main__":
    asyncio.run(main())
