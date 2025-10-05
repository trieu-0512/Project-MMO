from typing import Literal

import numpy as np
from stable_baselines3 import A2C, DDPG, PPO, SAC, TD3

RLAlgo = Literal["ppo", "sac", "a2c", "td3", "ddpg"]


class RLPolicy:
    def __init__(self, algo: RLAlgo, model_path: str):
        self.algo = algo.lower()
        if self.algo == "ppo":
            self.model = PPO.load(model_path)
        elif self.algo == "sac":
            self.model = SAC.load(model_path)
        elif self.algo == "a2c":
            self.model = A2C.load(model_path)
        elif self.algo == "td3":
            self.model = TD3.load(model_path)
        elif self.algo == "ddpg":
            self.model = DDPG.load(model_path)
        else:
            raise ValueError("Unsupported algo")

    def predict_action(self, obs: np.ndarray) -> int:
        action, _ = self.model.predict(obs, deterministic=True)
        if isinstance(action, np.ndarray):
            mapped = int(np.clip(round(float(action[0]) * 1.5 + 1), 0, 2))
        else:
            mapped = int(action)
        return mapped
