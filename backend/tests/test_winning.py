import random

from hexcoach.engine.actions import BuildCity, EndTurn
from hexcoach.engine.rules import (
    TURN_CAP,
    apply,
    is_terminal,
    legal_actions,
    new_game,
    victory_points,
    winner,
)
from hexcoach.engine.state import Phase


def place(state, vertex, player, level):
    state.vertex_owner[vertex] = player
    state.vertex_level[vertex] = level


def test_settlement_is_1_point_city_is_2_longest_road_is_2():
    state = new_game(seed=42)
    place(state, 0, 0, 1)
    place(state, 9, 0, 2)
    assert victory_points(state, 0) == 3
    state.longest_road_holder = 0
    assert victory_points(state, 0) == 5
    assert victory_points(state, 1) == 0


def nine_points_for_player_0():
    # 3 cities (6) + 3 settlements (3) = 9
    state = new_game(seed=42)
    state.phase = Phase.MAIN
    for v in (0, 9, 18):
        place(state, v, 0, 2)
    for v in (30, 40, 50):
        place(state, v, 0, 1)
    state.hands[0] = [0, 0, 0, 2, 3]
    state.bank = [19, 19, 19, 17, 16]
    return state


def test_reaching_10_points_ends_the_game_immediately():
    state = nine_points_for_player_0()
    assert not is_terminal(state)
    after = apply(state, BuildCity(30), random.Random(0))
    assert victory_points(after, 0) == 10
    assert is_terminal(after)
    assert winner(after) == 0
    assert legal_actions(after) == []


def test_no_winner_below_10():
    state = nine_points_for_player_0()
    assert winner(state) is None
    assert not is_terminal(state)


def at_turn_399(vps_levels):
    state = new_game(seed=42)
    state.phase = Phase.MAIN
    state.turn_number = TURN_CAP - 1
    for player, vertex, level in vps_levels:
        place(state, vertex, player, level)
    return state


def test_turn_cap_gives_the_win_to_the_leader():
    state = at_turn_399([(0, 0, 2), (1, 30, 1)])
    after = apply(state, EndTurn(), random.Random(0))
    assert after.turn_number == TURN_CAP
    assert is_terminal(after)
    assert winner(after) == 0


def test_turn_cap_with_a_tie_is_a_draw():
    state = at_turn_399([(0, 0, 2), (1, 30, 2)])
    after = apply(state, EndTurn(), random.Random(0))
    assert is_terminal(after)
    assert winner(after) is None
