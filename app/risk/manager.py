from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

import numpy as np

from app.core.config import get_settings

settings = get_settings()


@dataclass
class RiskState:
    campaign: str
    nav: float
    nav_spot: float
    nav_fut: float
    last_reset: datetime
    losses_streak: int = 0
    paused_until: Optional[datetime] = None

    def is_paused(self) -> bool:
        return self.paused_until is not None and datetime.utcnow() < self.paused_until


class RiskManager:
    def __init__(self) -> None:
        self.state: Dict[str, RiskState] = {}

    def ensure_state(self, campaign: str, nav_spot: float, nav_fut: float) -> RiskState:
        if campaign not in self.state:
            nav_total = nav_spot + nav_fut
            self.state[campaign] = RiskState(
                campaign=campaign,
                nav=nav_total,
                nav_spot=nav_spot,
                nav_fut=nav_fut,
                last_reset=datetime.utcnow(),
            )
        return self.state[campaign]

    def update_nav(self, campaign: str, nav_spot: float, nav_fut: float) -> None:
        state = self.ensure_state(campaign, nav_spot, nav_fut)
        state.nav = nav_spot + nav_fut
        state.nav_spot = nav_spot
        state.nav_fut = nav_fut

    def check_daily_stop(self, campaign: str, pnl_pct: float) -> bool:
        limit = settings.daily_stop_spot_pct if campaign == "SPOT" else settings.daily_stop_fut_pct
        if pnl_pct <= limit:
            state = self.state[campaign]
            state.paused_until = datetime.utcnow() + timedelta(hours=24)
            return True
        return False

    def register_loss(self, campaign: str) -> None:
        state = self.state.setdefault(
            campaign,
            RiskState(
                campaign=campaign,
                nav=0,
                nav_spot=0,
                nav_fut=0,
                last_reset=datetime.utcnow(),
            ),
        )
        state.losses_streak += 1
        if state.losses_streak >= 3:
            state.paused_until = datetime.utcnow() + timedelta(hours=24)

    def register_win(self, campaign: str) -> None:
        state = self.state.setdefault(
            campaign,
            RiskState(
                campaign=campaign,
                nav=0,
                nav_spot=0,
                nav_fut=0,
                last_reset=datetime.utcnow(),
            ),
        )
        state.losses_streak = 0

    def release_pause(self, campaign: str) -> None:
        state = self.state[campaign]
        state.paused_until = None

    def compute_position_size(
        self,
        campaign: str,
        nav: float,
        atr_pct: float,
        confidence: float,
        leverage: float = 1.0,
    ) -> Decimal:
        self.ensure_state(campaign, nav_spot=nav if campaign == "SPOT" else 0, nav_fut=nav if campaign == "FUT" else 0)
        risk_budget = settings.position_pct_max
        dynamic_factor = np.clip(confidence, 0.2, 1.0)
        atr_adjustment = max(atr_pct / 100, 0.01)
        capital = nav * risk_budget * dynamic_factor / atr_adjustment
        size = Decimal(str(capital * leverage))
        return size

    def atr_sl_tp(self, price: float, atr_value: float, side: str) -> tuple[float, float]:
        sl_offset = settings.atr_sl_mult * atr_value
        tp_offset = settings.atr_tp_mult * atr_value
        if side.upper() == "BUY":
            return max(price - sl_offset, 0), price + tp_offset
        return price + sl_offset, max(price - tp_offset, 0)

    def should_reduce_size(self, campaign: str) -> bool:
        state = self.state.get(campaign)
        if state is None:
            return False
        if state.losses_streak >= 3:
            return True
        if state.paused_until and datetime.utcnow() < state.paused_until:
            return True
        return False

    def cooldown_multiplier(self, campaign: str) -> float:
        return 0.5 if self.should_reduce_size(campaign) else 1.0


risk_manager = RiskManager()
