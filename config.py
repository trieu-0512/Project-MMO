import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
TRADING_MODE = os.getenv("TRADING_MODE", "PAPER").upper()

SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
INTERVAL = os.getenv("INTERVAL", "1m")

POSITION_PCT = float(os.getenv("POSITION_PCT", 0.2))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", 5))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.5))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", 1.0))
COOLDOWN_SEC = int(os.getenv("COOLDOWN_SEC", 30))

RL_MODEL_PATH = os.getenv("RL_MODEL_PATH", "models/ppo_btcusdt.zip")

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
