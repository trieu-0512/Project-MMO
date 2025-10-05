import argparse
import os
from datetime import datetime

import pandas as pd

from finrl.agents.stablebaselines3_models import DRLAgent
from finrl.env.env_stocktrading import StockTradingEnv
from finrl.marketdata.binance import BinanceProcessor

ALGOS = {
    "ppo": "ppo",
    "sac": "sac",
}


def fetch_binance(symbol: str, interval: str, start: str, end: str) -> pd.DataFrame:
    dp = BinanceProcessor()
    df = dp.fetch_data(symbol=symbol, interval=interval, start_date=start, end_date=end)
    df = df.rename(
        columns={
            "open_time": "date",
            "close": "close",
            "open": "open",
            "high": "high",
            "low": "low",
            "volume": "volume",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    df["tic"] = symbol
    return df[["date", "tic", "open", "high", "low", "close", "volume"]]


def build_env(df: pd.DataFrame, initial_amount: float = 10000, turbulence_threshold: int = 1_000_000):
    env = StockTradingEnv(
        df=df,
        initial_amount=initial_amount,
        turbulence_threshold=turbulence_threshold,
        risk_indicator_col="close",
        hmax=1_000_000,
        reward_scaling=1.0,
    )
    return env


def train(mode: str, symbols: list, interval: str, start: str, end: str, timesteps: int, save_dir: str):
    os.makedirs(save_dir, exist_ok=True)
    frames = [fetch_binance(sym, interval, start, end) for sym in symbols]
    df = pd.concat(frames).sort_values(["date", "tic"]).reset_index(drop=True)

    env = build_env(df)
    agent = DRLAgent(env=env)

    algo = "ppo" if mode == "spot" else "sac"
    model = agent.get_model(ALGOS[algo])

    trained = agent.train_model(model=model, tb_log_name=f"{algo}_{mode}", total_timesteps=timesteps)

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"{algo}_{mode}_{'_'.join(symbols)}_{stamp}.zip"
    out_path = os.path.join(save_dir, filename)
    trained.save(out_path)
    print("Saved:", out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["spot", "futures"], required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--save_dir", default="models")
    args = parser.parse_args()
    train(args.mode, args.symbols, args.interval, args.start, args.end, args.timesteps, args.save_dir)
