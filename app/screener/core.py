from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from app.core.config import get_settings

settings = get_settings()


@dataclass
class ScreenerResult:
    symbol: str
    score: float
    sharpe: float
    sortino: float
    atr_pct: float
    expected_return: float
    action: str
    atr: float
    rr: float
    last_price: float


def compute_returns(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change().fillna(0)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def sharpe_ratio(rets: pd.Series) -> float:
    if rets.std() == 0:
        return 0.0
    return (rets.mean() / rets.std()) * np.sqrt(len(rets))


def sortino_ratio(rets: pd.Series) -> float:
    downside = rets[rets < 0]
    if downside.std() == 0:
        return 0.0
    return (rets.mean() / downside.std()) * np.sqrt(len(rets))


def screen_symbol(symbol: str, df: pd.DataFrame, min_qvol: float, daily_fee: float) -> ScreenerResult | None:
    if df["quote_volume"].tail(24).mean() < min_qvol:
        return None
    rets = compute_returns(df)
    atr_series = atr(df)
    atr_pct = (atr_series.iloc[-1] / df["close"].iloc[-1]) * 100
    mean_ret = rets.tail(24).mean()
    sharpe = sharpe_ratio(rets.tail(72))
    sortino = sortino_ratio(rets.tail(72))
    rr = max(mean_ret * settings.atr_tp_mult, 0) / max(atr_series.iloc[-1] * settings.atr_sl_mult, 1e-8)
    score = (sharpe * 0.4) + (sortino * 0.4) + ((mean_ret * 100) * 0.2) - (daily_fee * 100)
    action = "HOLD"
    if mean_ret > daily_fee:
        action = "BUY"
    elif mean_ret < -daily_fee:
        action = "SELL"
    return ScreenerResult(
        symbol=symbol,
        score=float(score),
        sharpe=float(sharpe),
        sortino=float(sortino),
        atr_pct=float(atr_pct),
        expected_return=float(mean_ret),
        action=action,
        atr=float(atr_series.iloc[-1]),
        rr=float(rr),
        last_price=float(df["close"].iloc[-1]),
    )


def run_screener(data: Dict[str, pd.DataFrame], campaign: str, top_n: int = 5) -> List[ScreenerResult]:
    min_qvol = settings.screener_min_qvol_usdt
    fee = settings.fee_taker_spot if campaign == "SPOT" else settings.fee_taker_fut
    results: List[ScreenerResult] = []
    for symbol, df in data.items():
        result = screen_symbol(symbol, df, min_qvol=min_qvol, daily_fee=fee)
        if result and result.score >= 0:
            results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]


def serialize_results(results: Iterable[ScreenerResult]) -> List[Dict[str, float | str]]:
    return [
        {
            "symbol": r.symbol,
            "score": r.score,
            "sharpe": r.sharpe,
            "sortino": r.sortino,
            "atr_pct": r.atr_pct,
            "expected_return": r.expected_return,
            "action": r.action,
            "atr": r.atr,
            "rr": r.rr,
            "last_price": r.last_price,
        }
        for r in results
    ]
