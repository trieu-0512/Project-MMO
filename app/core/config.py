from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    trading_mode: str = Field(default="PAPER", alias="TRADING_MODE")
    spot_symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT"], alias="SPOT_SYMBOLS")
    fut_symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT"], alias="FUT_SYMBOLS")
    interval: str = Field(default="1h", alias="INTERVAL")
    db_url: str = Field(default="sqlite+aiosqlite:///./app.db", alias="DB_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rl_spot_model_path: str = Field(default="models/spot/ppo_spot.zip", alias="RL_SPOT_MODEL_PATH")
    rl_fut_model_path: str = Field(default="models/futures/sac_fut.zip", alias="RL_FUT_MODEL_PATH")
    daily_stop_spot_pct: float = Field(default=-3.0, alias="DAILY_STOP_SPOT_PCT")
    daily_stop_fut_pct: float = Field(default=-5.0, alias="DAILY_STOP_FUT_PCT")
    position_pct_max: float = Field(default=0.2, alias="POSITION_PCT_MAX")
    atr_sl_mult: float = Field(default=1.25, alias="ATR_SL_MULT")
    atr_tp_mult: float = Field(default=2.5, alias="ATR_TP_MULT")
    trail_atr_mult: float = Field(default=1.0, alias="TRAIL_ATR_MULT")
    fee_taker_spot: float = Field(default=0.0010, alias="FEE_TAKER_SPOT")
    fee_taker_fut: float = Field(default=0.0004, alias="FEE_TAKER_FUT")
    funding_alert: float = Field(default=0.0003, alias="FUNDING_ALERT")
    screener_min_qvol_usdt: float = Field(default=10_000_000, alias="SCREENER_MIN_QVOL_USDT")
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("spot_symbols", "fut_symbols", pre=True)
    def split_symbols(cls, v: str | List[str]) -> List[str]:  # type: ignore[override]
        if isinstance(v, str):
            return [sym.strip().upper() for sym in v.split(",") if sym.strip()]
        return [sym.upper() for sym in v]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
