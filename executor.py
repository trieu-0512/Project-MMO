from dataclasses import dataclass
from typing import Optional

from config import STOP_LOSS_PCT, TAKE_PROFIT_PCT, TRADING_MODE
from exchange import BinanceSpot


@dataclass
class Position:
    base_qty: float = 0.0
    avg_price: float = 0.0


class Executor:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.mode = TRADING_MODE
        self.ex = BinanceSpot(symbol)
        self.pos = Position()
        self.equity_usdt: Optional[float] = None

    def on_account(self, usdt_free: float, base_free: float, price: float) -> None:
        self.equity_usdt = usdt_free + base_free * price
        if self.pos.base_qty == 0:
            self.pos.avg_price = 0.0

    def _paper_buy(self, quote_amount: float, price: float) -> None:
        qty = quote_amount / price
        if self.pos.base_qty > 0:
            self.pos.avg_price = (
                self.pos.avg_price * self.pos.base_qty + price * qty
            ) / (self.pos.base_qty + qty)
        else:
            self.pos.avg_price = price
        self.pos.base_qty += qty
        print(f"[PAPER] BUY {qty:.6f} @ {price}")

    def _paper_sell(self, qty: float, price: float) -> None:
        qty = min(qty, self.pos.base_qty)
        self.pos.base_qty -= qty
        print(f"[PAPER] SELL {qty:.6f} @ {price}")
        if self.pos.base_qty == 0:
            self.pos.avg_price = 0.0

    def buy(self, quote_amount: float, price: Optional[float] = None) -> None:
        px = price or self.ex.get_price()
        if self.mode == "PAPER":
            self._paper_buy(quote_amount, px)
        else:
            resp = self.ex.market_buy(quote_amount)
            print("[LIVE] BUY resp:", resp)

    def sell(self, qty: float, price: Optional[float] = None) -> None:
        px = price or self.ex.get_price()
        if self.mode == "PAPER":
            self._paper_sell(qty, px)
        else:
            resp = self.ex.market_sell(qty)
            print("[LIVE] SELL resp:", resp)

    def check_sl_tp(self, price: float) -> None:
        if self.pos.base_qty <= 0 or self.pos.avg_price <= 0:
            return
        sl = self.pos.avg_price * (1 - STOP_LOSS_PCT / 100)
        tp = self.pos.avg_price * (1 + TAKE_PROFIT_PCT / 100)
        if price <= sl:
            print("[RISK] Stop-loss triggered")
            self.sell(self.pos.base_qty, price)
        elif price >= tp:
            print("[RISK] Take-profit triggered")
            self.sell(self.pos.base_qty, price)
