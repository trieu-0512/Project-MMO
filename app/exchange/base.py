from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from binance.error import ClientError
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential


class ExchangeError(RuntimeError):
    pass


class RateLimiter:
    def __init__(self, min_interval: float = 0.2) -> None:
        self.min_interval = min_interval
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.time()


def guarded_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    limiter: Optional[RateLimiter] = kwargs.pop("limiter", None)

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=8), stop=stop_after_attempt(3))
    def _inner() -> Any:
        if limiter:
            limiter.wait()
        return fn(*args, **kwargs)

    try:
        return _inner()
    except RetryError as exc:  # pragma: no cover - defensive
        raise ExchangeError(str(exc)) from exc
    except ClientError as exc:
        raise ExchangeError(f"Binance error {exc.error_code}: {exc.error_message}") from exc
