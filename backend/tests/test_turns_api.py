import random

from hexcoach.api.schemas import action_adapter, to_engine_action
from hexcoach.api.sessions import SessionStore
from hexcoach.api.turns import bot_step, bot_to_move, play_move
from hexcoach.bots.heuristic import HeuristicBot
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.rules import apply, is_terminal, legal_actions, new_game, player_to_move
from hexcoach.engine.state import Phase


def bot_game(seed, bots):
    return SessionStore().create(seed, -1, bots, new_game(seed))


def play_out(session):
    while bot_to_move(session):
        bot_step(session)


def logged_actions(session):
    for entry in session.log:
        fields = {k: v for k, v in entry.items() if k not in ("player", "roll")}
        yield entry["player"], to_engine_action(action_adapter.validate_python(fields))


def test_bots_play_to_the_end():
    session = bot_game(4, {0: HeuristicBot(), 1: HeuristicBot(), 2: HeuristicBot()})
    play_out(session)
    assert is_terminal(session.state)
    assert not bot_to_move(session)


def test_seed_and_log_replay_the_exact_game():
    # random bots draw from bot_rng, so the dice still match on replay
    session = bot_game(9, {0: RandomBot(), 1: RandomBot(), 2: RandomBot()})
    for _ in range(500):
        if not bot_to_move(session):
            break
        bot_step(session)

    rng, state = random.Random(9), new_game(9)
    for player, action in logged_actions(session):
        assert player == player_to_move(state)
        state = apply(state, action, rng)
    assert state == session.state


def test_rolls_are_logged():
    session = bot_game(2, {0: HeuristicBot(), 1: HeuristicBot(), 2: HeuristicBot()})
    play_out(session)
    rolls = [e["roll"] for e in session.log if e["type"] == "RollDice"]
    assert rolls and all(2 <= r <= 12 for r in rolls)


def test_bots_stop_when_the_human_must_move():
    session = SessionStore().create(5, 0, {1: HeuristicBot(), 2: HeuristicBot()}, new_game(5))
    assert not bot_to_move(session)
    play_move(session, legal_actions(session.state)[0])
    play_move(session, legal_actions(session.state)[0])
    play_out(session)
    # snake order 0 1 2 2 1 0: both bots place twice, then it's our second settlement
    assert player_to_move(session.state) == 0
    assert session.state.phase == Phase.SETUP_SETTLEMENT
    assert [e["player"] for e in session.log] == [0, 0, 1, 1, 2, 2, 2, 2, 1, 1]
