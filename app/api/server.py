from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Account, Alert, Position, Setting, Signal
from app.db.session import AsyncSessionLocal, get_session
from app.logging.journal import log_event

settings = get_settings()
app = FastAPI(title="Trading Bot API", version="1.0", openapi_url="/api/v1/openapi.json")

redis_client: redis.Redis | None = None


@app.on_event("startup")
async def startup() -> None:
    global redis_client
    redis_client = redis.from_url(settings.redis_url)


class PauseRequest(BaseModel):
    campaign: str
    seconds: int = 900


class CloseRequest(BaseModel):
    campaign: str
    symbol: Optional[str] = None


class RiskUpdateRequest(BaseModel):
    position_pct_max: Optional[float] = None
    daily_stop_pct: Optional[float] = None


class HedgeRequest(BaseModel):
    enable: bool
    max_ratio: float


class RetrainRequest(BaseModel):
    campaign: str
    timesteps: int


@app.get("/api/v1/health")
async def health() -> Dict[str, bool]:
    return {"ok": True}


@app.get("/api/v1/status")
async def status(session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    account = await session.get(Account, 1)
    positions = (await session.execute(select(Position).limit(50))).scalars().all()
    settings_rows = (await session.execute(select(Setting))).scalars().all()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "account": {
            "total": float(account.nav_total) if account else 0,
            "spot": float(account.nav_spot) if account else 0,
            "fut": float(account.nav_fut) if account else 0,
        },
        "positions": [
            {
                "id": pos.id,
                "symbol": pos.symbol,
                "side": pos.side,
                "qty": float(pos.qty),
                "sl": float(pos.sl or 0),
                "tp": float(pos.tp or 0),
                "status": pos.status,
                "updated_at": pos.updated_at.isoformat(),
            }
            for pos in positions
        ],
        "settings": {row.k: row.v for row in settings_rows},
    }


@app.post("/api/v1/pause")
async def pause(req: PauseRequest) -> Dict[str, Any]:
    key = f"pause:{req.campaign}"
    if redis_client is None:
        raise HTTPException(status_code=500, detail="Redis unavailable")
    await redis_client.set(key, req.seconds)
    log_event("pause", req.model_dump())
    return {"status": "paused", "campaign": req.campaign, "seconds": req.seconds}


@app.post("/api/v1/close")
async def close(req: CloseRequest) -> Dict[str, Any]:
    log_event("close", req.model_dump())
    return {"status": "closing", "campaign": req.campaign, "symbol": req.symbol}


@app.post("/api/v1/risk")
async def update_risk(req: RiskUpdateRequest, session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    if req.position_pct_max is not None:
        await session.execute(update(Setting).where(Setting.k == "position_pct_max").values(v=str(req.position_pct_max)))
    if req.daily_stop_pct is not None:
        await session.execute(update(Setting).where(Setting.k == "daily_stop_pct").values(v=str(req.daily_stop_pct)))
    await session.commit()
    log_event("risk_update", req.model_dump(exclude_none=True))
    return {"status": "ok"}


@app.post("/api/v1/hedge")
async def hedge(req: HedgeRequest) -> Dict[str, Any]:
    log_event("hedge_update", req.model_dump())
    return {"status": "ok", "hedge": req.model_dump()}


@app.post("/api/v1/screener/run")
async def screener_run(session: AsyncSession = Depends(get_session)) -> Dict[str, List[Dict[str, Any]]]:
    signals = (
        await session.execute(
            select(Signal).order_by(Signal.created_at.desc()).limit(20)
        )
    ).scalars().all()
    grouped: Dict[str, List[Dict[str, Any]]] = {"SPOT": [], "FUT": []}
    for signal in signals:
        grouped.setdefault(signal.campaign, []).append(
            {
                "symbol": signal.symbol,
                "score": signal.score,
                "action": signal.action,
                "atr_pct": signal.atr_pct,
                "expected_return": signal.exp_ret,
            }
        )
    return grouped


@app.get("/api/v1/signals/recent")
async def signals_recent(session: AsyncSession = Depends(get_session)) -> Dict[str, List[Dict[str, Any]]]:
    return await screener_run(session)


@app.get("/api/v1/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    if not settings.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    lines = [
        "# HELP bot_heartbeat_seconds Heartbeat timestamp",
        "# TYPE bot_heartbeat_seconds gauge",
    ]
    if redis_client is not None:
        heartbeat = await redis_client.get("bot:heartbeat")
        if heartbeat:
            value = heartbeat.decode() if isinstance(heartbeat, bytes) else heartbeat
            lines.append(f"bot_heartbeat_seconds {{}} {value}")
    return "\n".join(lines)


@app.post("/api/v1/retrain")
async def retrain(req: RetrainRequest) -> Dict[str, Any]:
    log_event("retrain_request", req.model_dump())
    return {"status": "scheduled", "campaign": req.campaign, "timesteps": req.timesteps}
