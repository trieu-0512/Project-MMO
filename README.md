# Auto Crypto Trading Bot (FinRL + Binance)

## 1. Cài đặt
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Chuẩn bị model RL (SB3)

* Bạn có thể train trước với FinRL/Stable-Baselines3 (PPO) để tạo file `models/ppo_btcusdt.zip`.
* Hoặc tạm **mock** một policy đơn giản rồi thay bằng RL sau.

## 3. Chạy bot (paper)

```bash
python bot.py
```

Mặc định `TRADING_MODE=PAPER` → bot **không** gửi lệnh thật, chỉ journal.

## 4. Bật live trading (rất cẩn thận)

* Chuyển `TRADING_MODE=LIVE` trong `.env`
* Đảm bảo API Key có quyền **Spot trading** và bật IP whitelist.
* Bắt buộc chạy nhỏ / giới hạn rủi ro, thử Testnet trước.

## 5. Lưu ý an toàn

* Giới hạn `POSITION_PCT`, `MAX_DAILY_LOSS_PCT`.
* Thử trên `INTERVAL=1m/5m` với số vốn nhỏ.
* Luôn có cơ chế dừng khẩn cấp (kill switch).
