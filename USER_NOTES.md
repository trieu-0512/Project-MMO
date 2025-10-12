# Yêu cầu của người dùng

Ứng dụng phải tuân thủ các nội dung sau và **không chỉnh sửa file này nếu không có yêu cầu trực tiếp từ người dùng**.

```json
{
  "title": "Auto Crypto Trading Bot (FinRL + Binance) — Full App",
  "language": "vi",
  "objective": "Sinh mã nguồn một ứng dụng hoàn chỉnh để giao dịch crypto tự động trên Binance (Spot + Futures) dùng FinRL (PPO/SAC), có screener, quản trị rủi ro, phí/slippage, daemon 24/24, API giám sát và web/mobile dashboard. Không dùng GPT.",
  "stack": {
    "backend": "Python 3.11 + FastAPI",
    "ai": "FinRL + Stable-Baselines3 (PPO cho Spot, SAC cho Futures)",
    "data": "PostgreSQL (OLTP) + Redis (cache/flags)",
    "runtime": "Docker Compose",
    "frontend": "Next.js (React) + Tailwind (web admin). Mobile: React Native (sau).",
    "logging": "Structured JSON logs + Prometheus metrics (tuỳ chọn)",
    "exchanges": "Binance Connector (Spot, Futures USDT-M)"
  },
  "ui_layout": {
    "resolution": "1920x1080",
    "layout_style": "widescreen, responsive, non-scroll",
    "main_navigation": {
      "type": "tabs",
      "position": "top_below_header",
      "tabs": [
        {
          "name": "Dashboard",
          "description": "Tổng quan: NAV, KPIs, equity curve, drawdown, trạng thái bot.",
          "widgets": [
            "NAV tổng + NAV Spot/Futures",
            "Equity curve & MaxDD",
            "KPIs: Sharpe, Sortino, Win rate, Profit Factor",
            "Uptime & trạng thái dịch vụ"
          ]
        },
        {
          "name": "Trading",
          "description": "Hoạt động giao dịch: vị thế mở, lịch sử lệnh, tín hiệu RL, screener.",
          "widgets": [
            "Bảng vị thế (symbol, qty, avg_price, PnL, SL/TP)",
            "Lịch sử lệnh gần nhất (time, side, size, price, fee, slippage)",
            "Tín hiệu RL (Buy/Sell/Hold, confidence)",
            "Screener Top-N (Sharpe/Sortino/ATR/RR)"
          ]
        },
        {
          "name": "System",
          "description": "Điều khiển & giám sát hệ thống: pause/resume, kill switch, cảnh báo, cấu hình rủi ro.",
          "widgets": [
            "Control panel (Pause/Resume/Kill Switch)",
            "Alert panel (funding cao, SL hit, API error, daily stop)",
            "Risk settings (position %, SL/TP multiplier, fee guard)",
            "Lịch retrain & trạng thái model"
          ]
        }
      ]
    },
    "design_rules": {
      "theme": "dark-light toggle",
      "font_family": "Inter, sans-serif",
      "component_style": {
        "card": "rounded-2xl, soft-shadow, padding-4",
        "button": "rounded-xl, hover-scale, smooth transition",
        "chart": "high-contrast"
      },
      "layout_grid": "12-column responsive grid",
      "padding": "16–24px",
      "no_scroll": true,
      "interaction": "Smooth tab switching without full page reload"
    },
    "responsive_behavior": {
      "desktop": "3-column layout",
      "tablet": "2-column layout with collapsible sidebar",
      "mobile": "1-column; tabs thành bottom bar"
    }
  },
  "frontend_stack": {
    "framework": "Next.js (React 18) + TailwindCSS + Recharts + Zustand",
    "components": {
      "Header": "Logo, tài khoản, nút bật/tắt bot",
      "Tabs": "Dashboard / Trading / System",
      "CardMetrics": "NAV, PnL, KPIs",
      "TradeTable": "Vị thế & lịch sử lệnh",
      "AlertPanel": "Cảnh báo hệ thống",
      "ControlPanel": "Pause/Resume/Kill/Hedge/Risk",
      "ChartPanel": "Giá & equity curve",
      "SettingsModal": "SL/TP, risk%, fee rate"
    },
    "api_endpoints": {
      "dashboard": "/api/v1/status",
      "trades": "/api/v1/orders/recent",
      "positions": "/api/v1/positions",
      "alerts": "/api/v1/alerts",
      "control_pause": "/api/v1/pause",
      "control_close": "/api/v1/close",
      "risk_update": "/api/v1/risk",
      "hedge": "/api/v1/hedge",
      "screener_run": "/api/v1/screener/run",
      "signals_recent": "/api/v1/signals/recent",
      "metrics": "/api/v1/metrics",
      "retrain": "/api/v1/retrain"
    }
  },
  "env": {
    "BINANCE_API_KEY": "",
    "BINANCE_API_SECRET": "",
    "TRADING_MODE": "PAPER",
    "SPOT_SYMBOLS": "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT",
    "FUT_SYMBOLS": "BTCUSDT,ETHUSDT",
    "INTERVAL": "1h",
    "DB_URL": "postgresql+psycopg2://user:pass@db:5432/trading",
    "REDIS_URL": "redis://redis:6379/0",
    "RL_SPOT_MODEL_PATH": "models/spot/ppo_spot.zip",
    "RL_FUT_MODEL_PATH": "models/futures/sac_fut.zip",
    "DAILY_STOP_SPOT_PCT": "-3",
    "DAILY_STOP_FUT_PCT": "-5",
    "POSITION_PCT_MAX": "0.2",
    "ATR_SL_MULT": "1.25",
    "ATR_TP_MULT": "2.5",
    "TRAIL_ATR_MULT": "1.0",
    "FEE_TAKER_SPOT": "0.0010",
    "FEE_TAKER_FUT": "0.0004",
    "FUNDING_ALERT": "0.0003",
    "SCREENER_MIN_QVOL_USDT": "10000000"
  },
  "features_core": [
    { "name": "Kết nối Binance (Spot + Futures)", "desc": "Client chuẩn, quản lý key trong .env, retry/backoff, ratelimit guard" },
    { "name": "Data Collector", "desc": "Thu OHLCV, volume, funding, trade count; lưu PostgreSQL; cache Redis" },
    { "name": "Screener", "desc": "Chọn Top-N theo Sharpe, Sortino, ATR%, RR; lọc thanh khoản/khối lượng" },
    { "name": "RL Inference (PPO/SAC)", "desc": "Nạp model SB3 (.zip), dự đoán BUY/HOLD/SELL (Spot) hoặc target exposure (Futures)" },
    { "name": "Executor + Risk Manager", "desc": "Tính size theo %NAV, đặt OCO (SL/TP) ATR-based, kiểm tra phí & ATR trước lệnh" },
    { "name": "Daemon 24/24", "desc": "Giám sát vị thế, trailing SL, daily stop, funding; heartbeat & auto-resume" },
    { "name": "Phí & Slippage Adjuster", "desc": "Tính phí thực tế, ước lượng slippage/spread, loại coin phí cao" },
    { "name": "Logger / Journal", "desc": "Ghi lệnh, PnL, drawdown, fee, funding, audit actions" }
  ],
  "features_advanced": [
    "Multi-campaign: Spot (60%) / Futures (40%) tách NAV & rule",
    "Auto-hedge (Futures): bật khi ATR%/funding/drawdown vượt ngưỡng",
    "Cooldown logic: sau 3 SL liên tiếp giảm risk/lệnh 50% trong 24h",
    "Dynamic sizing: risk = f(ATR, volatility, confidence)",
    "Funding optimizer: tránh giữ qua kỳ funding bất lợi",
    "ATR-based trailing SL",
    "Daily Stop / Kill switch",
    "Realistic reward: PnL sau phí + phạt volatility",
    "Backtest engine với phí/slippage",
    "Auto retrain weekly (script CLI)"
  ],
  "features_profit": [
    "Regime detection (Bull/Bear/Sideway) để hạ/tăng rủi ro",
    "Ensemble RL (chọn model theo hiệu suất gần đây)",
    "Cross-asset filter (corr > 0.9 → loại bớt)",
    "Volatility-scaled exposure",
    "Auto param tuning (SL/TP/λ_RL) bằng rolling backtest nhỏ",
    "Mean-reversion detector để tránh FOMO",
    "Portfolio optimizer (HRP/Markowitz) cho Spot vs Futures",
    "Multi-timeframe fusion (15m + 1h + 4h)",
    "Dynamic fee thresholds",
    "Partial exit logic (TP/2 chốt 50% + dời SL về Entry)"
  ],
  "kpis": [
    "Sharpe > 1.2",
    "Sortino > 1.5",
    "MaxDD < 10%",
    "Profit Factor > 1.5",
    "Hit rate 45–60%",
    "Fee ratio < 15%",
    "Funding impact < 0.1%/ngày",
    "Uptime > 99.5%"
  ],
  "db_schema": {
    "tables": {
      "accounts": ["id PK", "nav_total", "nav_spot", "nav_fut", "updated_at"],
      "positions": ["id PK", "campaign ENUM('SPOT','FUT')", "symbol", "side", "qty", "avg_price", "sl", "tp", "pnl", "status", "updated_at"],
      "orders": ["id PK", "symbol", "type", "side", "price", "qty", "maker_taker", "fee_asset", "fee_amount", "slippage_bps", "funding_fee", "status", "created_at"],
      "signals": ["id PK", "campaign", "symbol", "score", "atr_pct", "exp_ret", "action ENUM('BUY','SELL','HOLD')", "meta JSONB", "created_at", "state"],
      "alerts": ["id PK", "severity", "message", "context JSONB", "created_at"],
      "audits": ["id PK", "actor", "action", "payload JSONB", "ip", "created_at"],
      "settings": ["k PK", "v", "updated_at"]
    },
    "indexes": [
      "positions(symbol,status)",
      "orders(symbol,created_at)",
      "signals(campaign,created_at)"
    ]
  },
  "api_spec": {
    "prefix": "/api/v1",
    "routes": [
      { "method": "GET", "path": "/health", "desc": "Heartbeat" },
      { "method": "GET", "path": "/status", "desc": "NAV, positions, settings" },
      { "method": "POST", "path": "/pause", "body": { "campaign": "SPOT|FUT|ALL", "seconds": 900 } },
      { "method": "POST", "path": "/close", "body": { "campaign": "SPOT|FUT|ALL", "symbol": "optional" } },
      { "method": "POST", "path": "/risk", "body": { "position_pct_max": "0.2", "daily_stop_pct": "-3" } },
      { "method": "POST", "path": "/hedge", "body": { "enable": true, "max_ratio": 0.5 } },
      { "method": "POST", "path": "/screener/run", "body": {} },
      { "method": "GET", "path": "/signals/recent", "desc": "Last N proposals" },
      { "method": "GET", "path": "/metrics", "desc": "Prometheus text/plain" },
      { "method": "POST", "path": "/retrain", "body": { "campaign": "SPOT|FUT", "timesteps": 1000000 } }
    ]
  },
  "ai_training": {
    "spot_algo": "PPO",
    "futures_algo": "SAC",
    "interval": "1h",
    "obs_features": ["ret_1h", "ret_6h", "ret_24h", "vol_20", "ATR14_pct", "ema_gap", "RSI14_norm", "pos_pct", "cash_pct"],
    "reward": "return_t - lambda_vol * vol20 - fees",
    "lambda_vol": 0.7,
    "fees": { "spot_roundtrip": 0.0020, "fut_roundtrip": 0.0008, "funding_est": 0.0002 },
    "ppo_params": {
      "total_timesteps": 1000000,
      "n_steps": 2048,
      "batch_size": 2048,
      "gamma": 0.99,
      "gae_lambda": 0.95,
      "clip_range": 0.2,
      "learning_rate": 0.00025,
      "ent_coef": 0.008,
      "vf_coef": 0.5,
      "max_grad_norm": 0.5
    },
    "sac_params": {
      "total_timesteps": 1000000,
      "learning_rate": 0.0003,
      "buffer_size": 500000,
      "batch_size": 1024,
      "tau": 0.02,
      "gamma": 0.99,
      "ent_coef": "auto"
    },
    "walk_forward": {
      "train_months": 12,
      "val_months": 3,
      "test_months": 3,
      "retrain_frequency_days": 7
    }
  },
  "services": [
    { "name": "bot-daemon", "cmd": "python -m app.bot.daemon", "restart": "always" },
    { "name": "scheduler", "cmd": "python -m app.bot.scheduler", "restart": "always" },
    { "name": "api", "cmd": "uvicorn app.api.server:app --host 0.0.0.0 --port 8000", "restart": "unless-stopped" },
    { "name": "db", "image": "postgres:15" },
    { "name": "redis", "image": "redis:7" }
  ],
  "files": [
    { "path": "app/api/server.py", "purpose": "FastAPI routes theo spec" },
    { "path": "app/exchange/binance_spot.py", "purpose": "Spot connector + filters" },
    { "path": "app/exchange/binance_fut.py", "purpose": "Futures isolated + funding" },
    { "path": "app/data/collector.py", "purpose": "Fetch OHLCV/volume/funding/trade count" },
    { "path": "app/screener/core.py", "purpose": "Sharpe/Sortino/ATR/RR scoring, Top-N" },
    { "path": "app/rl/policy_loader.py", "purpose": "Load SB3 models + predict" },
    { "path": "app/risk/manager.py", "purpose": "Sizing, OCO ATR, daily stop, cooldown" },
    { "path": "app/bot/daemon.py", "purpose": "Giám sát vị thế, trailing, alerts" },
    { "path": "app/bot/scheduler.py", "purpose": "Cron mỗi giờ: screener → inference → orders" },
    { "path": "app/execution/executor.py", "purpose": "Place/cancel orders, slippage guard" },
    { "path": "app/logging/journal.py", "purpose": "Order/PNL/fee/funding/audit logs" },
    { "path": "training/train_finrl.py", "purpose": "Train PPO/SAC với FinRL + SB3" },
    { "path": "docker/docker-compose.yml", "purpose": "Dựng services" },
    { "path": "frontend/pages/index.tsx", "purpose": "Dashboard web đơn giản (tabs non-scroll 1920×1080)" }
  ],
  "commands": {
    "dev_setup": [
      "python -m venv .venv && source .venv/bin/activate",
      "pip install -r requirements.txt",
      "cp .env.example .env"
    ],
    "train_spot": "python training/train_finrl.py --mode spot --symbols BTCUSDT ETHUSDT --interval 1h --start 2022-01-01 --end 2025-09-30 --timesteps 1000000 --save_dir models/spot",
    "train_fut": "python training/train_finrl.py --mode futures --symbols BTCUSDT ETHUSDT --interval 1h --start 2022-01-01 --end 2025-09-30 --timesteps 1000000 --save_dir models/futures",
    "run_bot": "docker compose up -d --build"
  },
  "acceptance_criteria": [
    "UI hiển thị đúng ở 1920x1080, không cần cuộn trang; 3 tabs hoạt động mượt.",
    "Dashboard hiển thị NAV/KPIs/Equity/Drawdown & trạng thái bot.",
    "Trading tab hiển thị vị thế, lịch sử lệnh, tín hiệu RL, screener Top-N.",
    "System tab cho phép pause/resume/kill và chỉnh risk, hiển thị cảnh báo.",
    "API /health trả về {ok:true}",
    "Screener trả về Top-N kèm score ≥ 0 cho symbol đủ thanh khoản",
    "Daemon log heartbeat mỗi 30s và trailing SL hoạt động",
    "Executor từ chối lệnh khi expected_ret_adj < phí",
    "Daily stop kích hoạt đúng ngưỡng và pause chiến dịch",
    "Train script tạo file model .zip và bot load được"
  ],
  "notes": "Không sử dụng GPT/LLM. Tập trung FinRL + SB3. Ưu tiên PAPER trước LIVE. Đặt OCO server-side khi sàn hỗ trợ; nếu không, daemon đảm nhiệm SL/TP nội bộ."
}
```

