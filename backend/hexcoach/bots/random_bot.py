"""Picks uniformly from the legal moves. The baseline every other bot must beat."""

import random

from hexcoach.engine.actions import Action
from hexcoach.engine.rules import legal_actions
from hexcoach.engine.state import GameState


class RandomBot:
    def choose(self, state: GameState, rng: random.Random) -> Action:
        return rng.choice(legal_actions(state))
