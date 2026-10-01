import json
import random

import pytest
from pydantic import ValidationError

from hexcoach.api.schemas import action_adapter, action_to_json, state_to_json, to_engine_action
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.actions import BuildRoad, Discard, PlaceSetupRoad
from hexcoach.engine.rules import apply, is_terminal, legal_actions, new_game


def round_trip(action):
    return to_engine_action(
        action_adapter.validate_python(json.loads(json.dumps(action_to_json(action))))
    )


def test_every_move_in_real_games_survives_a_json_round_trip():
    bot, seen = RandomBot(), set()
    for seed in range(5):
        rng = random.Random(seed)
        state = new_game(seed)
        while not is_terminal(state):
            for action in legal_actions(state):
                assert round_trip(action) == action
                seen.add(type(action).__name__)
            state = apply(state, bot.choose(state, rng), rng)
    assert len(seen) == 11


def test_discard_counts_come_back_as_a_tuple():
    assert round_trip(Discard((1, 0, 2, 0, 1))) == Discard((1, 0, 2, 0, 1))


@pytest.mark.parametrize(
    "bad",
    [
        {"type": "BuildRoad", "edge": "banana"},
        {"type": "BuildRoad", "edge": 72},
        {"type": "BuildRoad", "edge": -1},
        {"type": "BuildRoad"},
        {"type": "Teleport"},
        {"type": "Discard", "counts": [1, 2]},
        {"type": "BankTrade", "give": 5, "get": 0},
        {"edge": 3},
    ],
)
def test_malformed_moves_are_rejected(bad):
    with pytest.raises(ValidationError):
        action_adapter.validate_python(bad)


def test_state_json_is_plain_json_and_matches_the_engine():
    state = new_game(42)
    data = json.loads(json.dumps(state_to_json(state)))
    assert data["phase"] == "SETUP_SETTLEMENT"
    assert data["playerToMove"] == 0
    assert len(data["vertexOwner"]) == 54 and len(data["edgeOwner"]) == 72
    assert data["legal"]["settlement"] == list(range(54))


def test_legal_spots_match_legal_actions():
    rng = random.Random(3)
    state = new_game(3)
    for _ in range(300):
        moves = legal_actions(state)
        roads = sorted(a.edge for a in moves if isinstance(a, BuildRoad | PlaceSetupRoad))
        assert state_to_json(state)["legal"]["road"] == roads
        if is_terminal(state):
            break
        state = apply(state, RandomBot().choose(state, rng), rng)
