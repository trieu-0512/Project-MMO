import logging
from typing import Any, Dict, Optional

from binance.spot import Spot

from config import BINANCE_API_KEY, BINANCE_API_SECRET

logger = logging.getLogger(__name__)


class BinanceSpot:
    """Thin wrapper around the Binance Spot REST client."""

    def __init__(self, symbol: str, client: Optional[Spot] = None):
        self.symbol = symbol
        self.client = client or Spot(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
        self.filters = self._load_symbol_filters()

    def _load_symbol_filters(self) -> Dict[str, Any]:
        try:
            info = self.client.exchange_info(symbol=self.symbol)
            sym = info["symbols"][0]
            filters = {f["filterType"]: f for f in sym["filters"]}
            return filters
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("Failed to load symbol filters for %s: %s", self.symbol, exc)
            return {}

    def _round_step(self, qty: float) -> float:
        if not self.filters:
            return float(f"{qty:.8f}")
        step = float(self.filters["LOT_SIZE"]["stepSize"])
        precision = max(0, str(step)[::-1].find("."))
        return float(f"{qty:.{precision}f}")

    def _round_tick(self, price: float) -> float:
        if not self.filters:
            return float(f"{price:.8f}")
        tick = float(self.filters["PRICE_FILTER"]["tickSize"])
        precision = max(0, str(tick)[::-1].find("."))
        return float(f"{price:.{precision}f}")

    def get_price(self) -> float:
        ticker = self.client.ticker_price(self.symbol)
        return float(ticker["price"])

    def get_balance(self, asset: str) -> float:
        account = self.client.account()
        for balance in account.get("balances", []):
            if balance["asset"] == asset:
                return float(balance["free"])
        return 0.0

    def market_buy(self, quote_amount: float) -> Dict[str, Any]:
        price = self.get_price()
        qty = quote_amount / price
        qty = self._round_step(qty)
        return self.client.new_order(symbol=self.symbol, side="BUY", type="MARKET", quantity=qty)

    def market_sell(self, base_qty: float) -> Dict[str, Any]:
        qty = self._round_step(base_qty)
        return self.client.new_order(symbol=self.symbol, side="SELL", type="MARKET", quantity=qty)
