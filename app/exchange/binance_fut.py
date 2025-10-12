from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from binance.um_futures import UMFutures

from app.core.config import get_settings
from app.exchange.base import RateLimiter, guarded_call

settings = get_settings()


class BinanceFuturesGateway:
    def __init__(self) -> None:
        self.client = UMFutures(key=settings.binance_api_key, secret=settings.binance_api_secret)
        self.limiter = RateLimiter(min_interval=0.1)

    def server_time(self) -> datetime:
        data = guarded_call(self.client.time, limiter=self.limiter)
        return datetime.fromtimestamp(data["serverTime"] / 1000)

    def account_info(self) -> Dict[str, Any]:
        return guarded_call(self.client.account, limiter=self.limiter)

    def klines(self, symbol: str, interval: str, limit: int = 500) -> List[List[Any]]:
        return guarded_call(self.client.klines, symbol=symbol, interval=interval, limit=limit, limiter=self.limiter)

    def funding_rate(self, symbol: str) -> Dict[str, Any]:
        result = guarded_call(self.client.funding_rate, symbol=symbol, limit=1, limiter=self.limiter)
        return result[0] if result else {}

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = "MARKET",
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        reduce_only: bool | None = None,
        position_side: str | None = None,
        time_in_force: str | None = None,
        new_client_order_id: str | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": f"{quantity.normalize():f}",
        }
        if price is not None:
            params["price"] = f"{price.normalize():f}"
        if stop_price is not None:
            params["stopPrice"] = f"{stop_price.normalize():f}"
        if reduce_only is not None:
            params["reduceOnly"] = "true" if reduce_only else "false"
        if position_side is not None:
            params["positionSide"] = position_side
        if time_in_force is not None:
            params["timeInForce"] = time_in_force
        if new_client_order_id:
            params["newClientOrderId"] = new_client_order_id

        return guarded_call(self.client.new_order, limiter=self.limiter, **params)

    def cancel_order(self, symbol: str, order_id: int | None = None, client_order_id: str | None = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id is not None:
            params["origClientOrderId"] = client_order_id
        return guarded_call(self.client.cancel_order, limiter=self.limiter, **params)
