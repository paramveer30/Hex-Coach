"""The interface every bot implements."""

import random
from typing import Protocol

from hexcoach.engine.actions import Action
from hexcoach.engine.state import GameState


class Bot(Protocol):
    def choose(self, state: GameState, rng: random.Random) -> Action: ...
