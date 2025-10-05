from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskState:
    start_equity: float
    max_daily_loss_pct: float
    cooldown_sec: int
    last_trade_ts: Optional[float] = None

    def allow_trade(self, now_ts: float, cur_equity: float) -> bool:
        drawdown = 100.0 * (1.0 - cur_equity / max(self.start_equity, 1e-6))
        if drawdown > self.max_daily_loss_pct:
            return False
        if self.last_trade_ts is not None and (now_ts - self.last_trade_ts) < self.cooldown_sec:
            return False
        return True

    def mark_trade(self, now_ts: float) -> None:
        self.last_trade_ts = now_ts


def position_size(equity_usdt: float, pct: float) -> float:
    return max(0.0, equity_usdt * pct)
