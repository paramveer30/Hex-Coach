import random

import pytest

from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.invariants import (
    assert_invariants,
    check_distance_rule,
    check_longest_road,
    check_pieces,
    check_resources,
    check_roads_connected,
    check_robber,
)
from hexcoach.engine.rules import apply, is_terminal, new_game


def test_fresh_game_is_fine():
    check_resources(new_game(seed=42))


def test_cards_moved_from_bank_to_hand_are_fine():
    state = new_game(seed=42)
    state.bank[3] -= 4
    state.hands[1][3] += 4
    check_resources(state)


def test_card_created_from_nothing_fails():
    state = new_game(seed=42)
    state.hands[0][2] += 1
    with pytest.raises(AssertionError):
        check_resources(state)


def test_card_destroyed_fails():
    state = new_game(seed=42)
    state.bank[4] -= 1
    with pytest.raises(AssertionError):
        check_resources(state)


def test_negative_hand_fails_even_if_the_total_is_19():
    state = new_game(seed=42)
    state.hands[0][0] = -1
    state.bank[0] = 20
    with pytest.raises(AssertionError):
        check_resources(state)


def test_negative_bank_fails_even_if_the_total_is_19():
    state = new_game(seed=42)
    state.hands[2][1] = 20
    state.bank[1] = -1
    with pytest.raises(AssertionError):
        check_resources(state)


def test_piece_count_mismatch_fails():
    state = new_game(seed=42)
    state.edge_owner[0] = 0
    with pytest.raises(AssertionError, match="roads"):
        check_pieces(state)


def test_neighboring_buildings_fail():
    state = new_game(seed=42)
    state.vertex_owner[0], state.vertex_level[0] = 0, 1
    state.vertex_owner[3], state.vertex_level[3] = 1, 1
    with pytest.raises(AssertionError, match="neighboring"):
        check_distance_rule(state)


def test_floating_road_fails():
    state = new_game(seed=42)
    state.edge_owner[40] = 0
    with pytest.raises(AssertionError, match="not connected"):
        check_roads_connected(state)


def test_road_cut_by_an_opponent_is_still_connected():
    # P0 settlement at 21, roads 21-16-11; P1 then builds on 16 in the middle
    state = new_game(seed=42)
    state.vertex_owner[21], state.vertex_level[21] = 0, 1
    state.edge_owner[23] = 0
    state.edge_owner[18] = 0
    state.vertex_owner[16], state.vertex_level[16] = 1, 1
    check_roads_connected(state)


def test_stale_longest_road_length_fails():
    state = new_game(seed=42)
    state.vertex_owner[21], state.vertex_level[21] = 0, 1
    state.edge_owner[23] = 0
    with pytest.raises(AssertionError, match="stored 0, actual 1"):
        check_longest_road(state)


def test_robber_off_the_board_fails():
    state = new_game(seed=42)
    state.robber_hex = 19
    with pytest.raises(AssertionError, match="robber"):
        check_robber(state)


def test_invariants_hold_through_real_games():
    bot = RandomBot()
    for seed in range(20):
        rng = random.Random(seed)
        state = new_game(seed)
        while not is_terminal(state):
            state = apply(state, bot.choose(state, rng), rng)
            assert_invariants(state)
