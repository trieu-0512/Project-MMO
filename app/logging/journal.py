from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(LOG_DIR / "bot.jsonl", serialize=True, level="INFO")


def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    entry = {
        "type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.bind(event=event_type).info(json.dumps(entry))
