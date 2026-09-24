import random

from hypothesis import given, settings
from hypothesis import strategies as st

from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.invariants import assert_invariants
from hexcoach.engine.rules import apply, is_terminal, new_game
from hexcoach.sim.runner import play_game

seeds = st.integers(min_value=0, max_value=2**32 - 1)
bot = RandomBot()


@settings(max_examples=40, deadline=None)
@given(seed=seeds)
def test_random_games_never_break_an_invariant(seed):
    rng = random.Random(seed)
    state = new_game(seed)
    assert_invariants(state)
    while not is_terminal(state):
        state = apply(state, bot.choose(state, rng), rng)
        assert_invariants(state)


@settings(max_examples=20, deadline=None)
@given(seed=seeds)
def test_apply_never_changes_its_input(seed):
    rng = random.Random(seed)
    state = new_game(seed)
    while not is_terminal(state):
        before = state.clone()
        after = apply(state, bot.choose(state, rng), rng)
        assert state == before
        state = after


@settings(max_examples=20, deadline=None)
@given(seed=seeds)
def test_same_seed_same_game(seed):
    assert play_game([bot] * 3, seed) == play_game([bot] * 3, seed)
