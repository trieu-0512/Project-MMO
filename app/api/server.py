from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Account, Alert, Order, Position, Setting, Signal
from app.db.session import get_session
from app.logging.journal import log_event

settings = get_settings()
app = FastAPI(title="Trading Bot API", version="1.0", openapi_url="/api/v1/openapi.json")

redis_client: redis.Redis | None = None
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup() -> None:
    global redis_client
    redis_client = redis.from_url(settings.redis_url)


@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


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
    positions = (await session.execute(select(Position).order_by(Position.updated_at.desc()).limit(100))).scalars().all()
    alerts = (await session.execute(select(Alert).order_by(Alert.created_at.desc()).limit(10))).scalars().all()
    settings_rows = (await session.execute(select(Setting))).scalars().all()

    settings_map: Dict[str, str] = {row.k: row.v for row in settings_rows}
    kpis: Dict[str, float] = {}
    for key, value in settings_map.items():
        if key.startswith("kpi."):
            metric = key.split(".", 1)[1]
            try:
                kpis[metric] = float(value)
            except (TypeError, ValueError):
                continue

    equity_curve: List[Dict[str, Any]] = []
    equity_raw = settings_map.get("equity_curve")
    if equity_raw:
        try:
            parsed = json.loads(equity_raw)
            if isinstance(parsed, list):
                equity_curve = parsed
        except json.JSONDecodeError:
            equity_curve = []

    nav_total = float(account.nav_total) if account else 0.0
    nav_spot = float(account.nav_spot) if account else 0.0
    nav_fut = float(account.nav_fut) if account else 0.0
    open_positions = sum(1 for pos in positions if getattr(pos, "status", "OPEN") == "OPEN")
    session_pnl = sum(float(getattr(pos, "pnl", 0) or 0) for pos in positions if getattr(pos, "status", "OPEN") == "OPEN")
    session_pnl_pct = (session_pnl / nav_total * 100) if nav_total else 0.0
    nav_change_pct = float(settings_map.get("nav_change_pct", 0) or 0)
    critical_alerts = sum(1 for alert in alerts if alert.severity == "CRITICAL")

    heartbeat_iso: Optional[str] = None
    if redis_client is not None:
        heartbeat = await redis_client.get("bot:heartbeat")
        if heartbeat:
            value = heartbeat.decode() if isinstance(heartbeat, bytes) else str(heartbeat)
            try:
                heartbeat_iso = datetime.fromtimestamp(float(value)).isoformat()
            except ValueError:
                heartbeat_iso = value

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "account": {
            "total": nav_total,
            "spot": nav_spot,
            "fut": nav_fut,
        },
        "session_pnl": session_pnl,
        "session_pnl_pct": session_pnl_pct,
        "nav_change_pct": nav_change_pct,
        "open_positions": open_positions,
        "critical_alerts": critical_alerts,
        "positions": [
            {
                "id": pos.id,
                "symbol": pos.symbol,
                "side": pos.side,
                "campaign": pos.campaign,
                "qty": float(pos.qty),
                "avg_price": float(getattr(pos, "avg_price", 0) or 0),
                "pnl": float(getattr(pos, "pnl", 0) or 0),
                "sl": float(pos.sl or 0) if pos.sl is not None else None,
                "tp": float(pos.tp or 0) if pos.tp is not None else None,
                "status": pos.status,
                "updated_at": pos.updated_at.isoformat(),
            }
            for pos in positions
        ],
        "alerts": [
            {
                "id": alert.id,
                "severity": alert.severity,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ],
        "heartbeat": heartbeat_iso,
        "db_latency": float(settings_map.get("db_latency_ms", 0) or 0),
        "kpis": kpis,
        "equity_curve": equity_curve,
        "settings": settings_map,
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


@app.get("/api/v1/positions")
async def positions_endpoint(session: AsyncSession = Depends(get_session)) -> List[Dict[str, Any]]:
    positions = (
        await session.execute(
            select(Position).order_by(Position.updated_at.desc()).limit(100)
        )
    ).scalars().all()
    return [
        {
            "id": pos.id,
            "campaign": pos.campaign,
            "symbol": pos.symbol,
            "side": pos.side,
            "qty": float(pos.qty),
            "avg_price": float(getattr(pos, "avg_price", 0) or 0),
            "pnl": float(getattr(pos, "pnl", 0) or 0),
            "sl": float(pos.sl or 0) if pos.sl is not None else None,
            "tp": float(pos.tp or 0) if pos.tp is not None else None,
            "status": pos.status,
            "updated_at": pos.updated_at.isoformat(),
        }
        for pos in positions
    ]


@app.get("/api/v1/orders/recent")
async def orders_recent(
    limit: int = 20, session: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    orders = (
        await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "type": order.type,
            "price": float(order.price or 0) if order.price is not None else None,
            "qty": float(order.qty),
            "maker_taker": order.maker_taker,
            "fee_asset": order.fee_asset,
            "fee_amount": float(order.fee_amount or 0) if order.fee_amount is not None else None,
            "slippage_bps": float(order.slippage_bps or 0) if order.slippage_bps is not None else None,
            "funding_fee": float(order.funding_fee or 0) if order.funding_fee is not None else None,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        }
        for order in orders
    ]


@app.get("/api/v1/alerts")
async def alerts_endpoint(session: AsyncSession = Depends(get_session)) -> List[Dict[str, Any]]:
    alerts = (
        await session.execute(select(Alert).order_by(Alert.created_at.desc()).limit(20))
    ).scalars().all()
    return [
        {
            "id": alert.id,
            "severity": alert.severity,
            "message": alert.message,
            "context": alert.context,
            "created_at": alert.created_at.isoformat(),
        }
        for alert in alerts
    ]


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
