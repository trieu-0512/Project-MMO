from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Float, Integer, Numeric, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    nav_total = Column(Numeric(18, 8), nullable=False, default=0)
    nav_spot = Column(Numeric(18, 8), nullable=False, default=0)
    nav_fut = Column(Numeric(18, 8), nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PositionStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    campaign = Column(Enum("SPOT", "FUT", name="campaign_enum"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum("LONG", "SHORT", name="side_enum"), nullable=False)
    qty = Column(Numeric(28, 12), nullable=False)
    avg_price = Column(Numeric(18, 8), nullable=False)
    sl = Column(Numeric(18, 8), nullable=True)
    tp = Column(Numeric(18, 8), nullable=True)
    pnl = Column(Numeric(18, 8), nullable=False, default=0)
    status = Column(String(20), nullable=False, default=PositionStatus.OPEN)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    side = Column(String(20), nullable=False)
    price = Column(Numeric(18, 8), nullable=True)
    qty = Column(Numeric(28, 12), nullable=False)
    maker_taker = Column(String(10), nullable=True)
    fee_asset = Column(String(10), nullable=True)
    fee_amount = Column(Numeric(18, 8), nullable=True)
    slippage_bps = Column(Float, nullable=True)
    funding_fee = Column(Numeric(18, 8), nullable=True)
    status = Column(String(20), nullable=False, default="NEW")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class SignalState:
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    campaign = Column(String(10), nullable=False)
    symbol = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    atr_pct = Column(Float, nullable=False)
    exp_ret = Column(Float, nullable=False)
    action = Column(Enum("BUY", "SELL", "HOLD", name="signal_action_enum"), nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    state = Column(String(20), nullable=False, default=SignalState.PENDING)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    severity = Column(Enum("INFO", "WARN", "CRITICAL", name="alert_severity"), nullable=False)
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True)
    actor = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    k = Column(String(50), primary_key=True)
    v = Column(String(255), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
