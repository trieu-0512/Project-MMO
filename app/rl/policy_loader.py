from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.base_class import BaseAlgorithm

from app.core.config import get_settings

settings = get_settings()


class PolicyRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, BaseAlgorithm] = {}

    def load(self, campaign: str) -> BaseAlgorithm:
        if campaign in self._registry:
            return self._registry[campaign]
        model_path = settings.rl_spot_model_path if campaign == "SPOT" else settings.rl_fut_model_path
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        if campaign == "SPOT":
            model = PPO.load(path)
        else:
            model = SAC.load(path)
        self._registry[campaign] = model
        return model

    def predict(self, campaign: str, obs: np.ndarray) -> np.ndarray:
        model = self.load(campaign)
        action, _ = model.predict(obs, deterministic=True)
        return action


registry = PolicyRegistry()
