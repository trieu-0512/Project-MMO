# Auto Crypto Trading Bot (FinRL + Binance)

Ứng dụng giao dịch tự động đa chiến dịch (Spot/Futures) sử dụng FinRL + Stable-Baselines3 cho inference, FastAPI cho API điều khiển và dashboard Python (FastAPI + Jinja2 + HTMX + TailwindCSS).

## Thành phần chính

| Module | Mô tả |
| --- | --- |
| `app/exchange/` | Kết nối Binance Spot/Futures với retry, ratelimit |
| `app/data/collector.py` | Thu thập OHLCV, funding và lưu cache Redis |
| `app/screener/core.py` | Tính Sharpe/Sortino/ATR%, chọn Top-N theo score |
| `app/rl/policy_loader.py` | Nạp mô hình PPO/SAC từ Stable-Baselines3 |
| `app/risk/manager.py` | Quản trị rủi ro, daily stop, ATR SL/TP, cooldown |
| `app/execution/executor.py` | Kiểm tra phí/slippage & đặt lệnh OCO |
| `app/bot/daemon.py` | Daemon giám sát 24/24, trailing SL, heartbeat |
| `app/bot/scheduler.py` | Chu trình mỗi giờ: collect → screener → RL → orders |
| `app/api/server.py` | FastAPI `/api/v1` (health, risk, pause, signals, metrics) |
| `frontend/pages/index.tsx` | Dashboard Python-rendered (HTMX + TailwindCSS) hiển thị NAV, positions, signals |

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Điền API Key Binance hoặc để rỗng khi chạy PAPER.

## Khởi tạo cơ sở dữ liệu

```bash
python -m app.db.init_db
```

## Train mô hình RL

```bash
# Spot (PPO)
python training/train_finrl.py --mode spot --symbols BTCUSDT ETHUSDT \
  --interval 1h --start 2022-01-01 --end 2025-09-30 --timesteps 1000000 \
  --save_dir models/spot

# Futures (SAC)
python training/train_finrl.py --mode futures --symbols BTCUSDT ETHUSDT \
  --interval 1h --start 2022-01-01 --end 2025-09-30 --timesteps 1000000 \
  --save_dir models/futures
```

## Chạy bot bằng Docker Compose

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Các service:

* `bot-daemon`: Heartbeat, trailing SL, daily stop.
* `scheduler`: Thu thập dữ liệu, screener, inference, đặt lệnh.
* `api`: FastAPI điều khiển & metrics.
* `db`: PostgreSQL lưu NAV, positions, signals, alerts.
* `redis`: Cache dữ liệu & cờ điều khiển.

Dashboard truy cập tại `http://localhost:8000` (proxy qua Next.js khi triển khai) hoặc sử dụng API trực tiếp.

## Lưu ý vận hành

* Giữ `TRADING_MODE=PAPER` cho đến khi hoàn tất kiểm thử.
* Tải mô hình RL vào `models/spot/ppo_spot.zip` và `models/futures/sac_fut.zip`.
* Theo dõi log JSON tại `logs/bot.jsonl` và metrics `/api/v1/metrics`.
* Cấu hình lại các ngưỡng risk trong `.env` hoặc API `/api/v1/risk`.
