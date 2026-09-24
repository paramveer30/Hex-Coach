import random

import pytest

from hexcoach.bots.heuristic import HeuristicBot, vertex_score
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.actions import MoveRobber
from hexcoach.engine.geometry import HEX_VERTICES
from hexcoach.engine.rules import apply, is_terminal, legal_actions, new_game, player_to_move
from hexcoach.sim.runner import play_game


@pytest.mark.parametrize("bot", [RandomBot(), HeuristicBot()], ids=["random", "heuristic"])
def test_bot_only_returns_legal_actions(bot):
    for seed in range(200):
        rng = random.Random(seed)
        state = new_game(seed)
        while not is_terminal(state):
            action = bot.choose(state, rng)
            assert action in legal_actions(state), f"seed {seed}: {action} not legal"
            state = apply(state, action, rng)


def test_heuristic_beats_two_random_bots_over_90_percent():
    wins = 0
    for seed in range(200):
        result = play_game([HeuristicBot(), RandomBot(), RandomBot()], seed)
        if result.winner is not None and result.seats[result.winner] == "HeuristicBot":
            wins += 1
    assert wins / 200 > 0.90


def test_heuristic_opens_on_the_best_scoring_spot():
    state = new_game(seed=42)
    choice = HeuristicBot().choose(state, random.Random(0))
    best = max(range(54), key=lambda v: vertex_score(state, v, set()))
    assert vertex_score(state, choice.vertex, set()) == vertex_score(state, best, set())


def test_heuristic_never_robs_itself_when_it_can_avoid_it():
    for seed in range(30):
        rng = random.Random(seed)
        state = new_game(seed)
        bot = HeuristicBot()
        while not is_terminal(state):
            action = bot.choose(state, rng)
            if isinstance(action, MoveRobber):
                me = player_to_move(state)
                safe = [
                    a
                    for a in legal_actions(state)
                    if not any(state.vertex_owner[v] == me for v in HEX_VERTICES[a.hex])
                ]
                if safe:
                    assert action in safe
            state = apply(state, action, rng)
