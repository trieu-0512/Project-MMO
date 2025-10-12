from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
from finrl.apps import config
from finrl.apps.env import StockTradingEnv
from finrl.marketdata.yahoodownloader import YahooDownloader
from stable_baselines3 import PPO, SAC


class BinanceLikeEnv(StockTradingEnv):
    def __init__(self, df: pd.DataFrame, **kwargs) -> None:
        kwargs.setdefault("reward_scaling", 1e-4)
        super().__init__(df=df, **kwargs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FinRL training wrapper")
    parser.add_argument("--mode", choices=["spot", "futures"], required=True)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--save_dir", type=str, default="models")
    return parser.parse_args()


def load_data(symbols: List[str], start: str, end: str) -> pd.DataFrame:
    downloader = YahooDownloader(start_date=start, end_date=end, ticker_list=symbols)
    df = downloader.fetch_data()
    df.sort_values(["date", "tic"], inplace=True)
    return df


def train(args: argparse.Namespace) -> None:
    df = load_data(args.symbols, args.start, args.end)
    env_kwargs = config.INDICATORS.copy()
    env_kwargs.update({"hmax": 100, "initial_amount": 100000, "buy_cost_pct": 0.001, "sell_cost_pct": 0.001})
    env = BinanceLikeEnv(df=df, **env_kwargs)
    if args.mode == "spot":
        model = PPO("MlpPolicy", env, verbose=1)
    else:
        model = SAC("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=args.timesteps)
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    suffix = "ppo_spot" if args.mode == "spot" else "sac_fut"
    model.save(save_dir / f"{suffix}.zip")


if __name__ == "__main__":
    arguments = parse_args()
    train(arguments)
