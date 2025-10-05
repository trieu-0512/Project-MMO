import time
from typing import Tuple

import numpy as np
from binance.spot import Spot

from config import (
    COOLDOWN_SEC,
    INTERVAL,
    MAX_DAILY_LOSS_PCT,
    POSITION_PCT,
    RL_MODEL_PATH,
    SYMBOL,
)
from data_stream import CandleFeed
from executor import Executor
from risk import RiskState, position_size
from strategy_rl import RLPolicy


DEFAULT_STARTING_USDT = 10000.0


def build_observation(df, equity_usdt: float, pos_base_qty: float, price: float) -> np.ndarray:
    close = df["close"]
    ret_1 = (close.iloc[-1] / close.iloc[-2] - 1.0) if len(close) > 1 else 0.0
    ret_5 = (close.iloc[-1] / close.iloc[-6] - 1.0) if len(close) > 6 else 0.0
    vol_20 = close.pct_change().rolling(20).std().iloc[-1] if len(close) > 20 else 0.0
    pos_value = pos_base_qty * price
    pos_pct = pos_value / max(equity_usdt, 1e-6)
    cash_pct = max(0.0, 1.0 - pos_pct)
    obs = np.array([ret_1, ret_5, vol_20, pos_pct, cash_pct], dtype=np.float32)
    return obs


def fetch_initial_balances(client: Spot) -> Tuple[float, float]:  # pragma: no cover - network path
    try:
        account = client.account()
        usdt = next((float(b["free"]) for b in account["balances"] if b["asset"] == "USDT"), DEFAULT_STARTING_USDT)
        base = next((float(b["free"]) for b in account["balances"] if b["asset"] == SYMBOL[:-4]), 0.0)
        return usdt, base
    except Exception:
        return DEFAULT_STARTING_USDT, 0.0


def main() -> None:  # pragma: no cover - runtime loop
    print("Starting Auto Trading Bot (PAPER by default)…")
    feed = CandleFeed(SYMBOL, INTERVAL, limit=200)
    executor = Executor(SYMBOL)

    client = Spot()
    usdt_free, base_free = fetch_initial_balances(client)
    price = feed.latest_close()
    executor.on_account(usdt_free=usdt_free, base_free=base_free, price=price)

    risk = RiskState(
        start_equity=executor.equity_usdt or DEFAULT_STARTING_USDT,
        max_daily_loss_pct=MAX_DAILY_LOSS_PCT,
        cooldown_sec=COOLDOWN_SEC,
    )
    policy = RLPolicy("ppo", RL_MODEL_PATH)

    while True:
        df = feed.fetch()
        price = float(df["close"].iloc[-1])
        base_qty = executor.pos.base_qty
        equity = usdt_free + base_qty * price
        executor.on_account(usdt_free=usdt_free, base_free=base_qty, price=price)

        now = time.time()
        if not risk.allow_trade(now_ts=now, cur_equity=equity):
            executor.check_sl_tp(price)
            time.sleep(3)
            continue

        obs = build_observation(df, equity, base_qty, price)
        action = policy.predict_action(obs)

        if action == 2:
            quote_amt = position_size(equity, POSITION_PCT)
            if quote_amt > 10:
                executor.buy(quote_amt, price)
                usdt_free -= quote_amt
                risk.mark_trade(now)
        elif action == 0 and base_qty > 0.0:
            executor.sell(base_qty, price)
            usdt_free += base_qty * price
            base_qty = 0.0
            risk.mark_trade(now)

        executor.check_sl_tp(price)
        time.sleep(5)


if __name__ == "__main__":
    main()
