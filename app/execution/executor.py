from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Iterable, Optional

from app.exchange.binance_fut import BinanceFuturesGateway
from app.exchange.binance_spot import BinanceSpotGateway
from app.risk.manager import risk_manager


@dataclass
class OrderRequest:
    symbol: str
    side: str
    campaign: str
    price: float
    atr: float
    atr_pct: float
    confidence: float
    expected_return: float
    fee: float
    leverage: float = 1.0


class ExecutionResult:
    def __init__(self, accepted: bool, reason: Optional[str] = None, order_response: Optional[Dict] = None) -> None:
        self.accepted = accepted
        self.reason = reason
        self.order_response = order_response or {}


class TradeExecutor:
    def __init__(self) -> None:
        self.spot = BinanceSpotGateway()
        self.fut = BinanceFuturesGateway()

    def _gateway(self, campaign: str):
        return self.spot if campaign == "SPOT" else self.fut

    def execute(self, nav: float, req: OrderRequest) -> ExecutionResult:
        expected_after_fee = req.expected_return - req.fee
        if expected_after_fee <= 0:
            return ExecutionResult(False, reason="expected_ret_adj <= fee")
        multiplier = risk_manager.cooldown_multiplier(req.campaign)
        size = risk_manager.compute_position_size(
            campaign=req.campaign,
            nav=nav,
            atr_pct=req.atr_pct,
            confidence=req.confidence,
            leverage=req.leverage,
        ) * Decimal(str(multiplier))
        if size <= 0:
            return ExecutionResult(False, reason="size <= 0")
        sl, tp = risk_manager.atr_sl_tp(price=req.price, atr_value=req.atr, side=req.side)
        qty = size.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        order_resp = self._gateway(req.campaign).place_order(
            symbol=req.symbol,
            side=req.side,
            quantity=qty,
            order_type="MARKET",
        )
        order_resp["sl"] = sl
        order_resp["tp"] = tp
        order_resp["size"] = str(qty)
        return ExecutionResult(True, order_response=order_resp)

    def cancel_orders(self, campaign: str, symbol: str, order_ids: Iterable[int]) -> None:
        gateway = self._gateway(campaign)
        for oid in order_ids:
            gateway.cancel_order(symbol=symbol, order_id=oid)


executor = TradeExecutor()
