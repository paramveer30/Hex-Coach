import random

from hexcoach.engine.actions import BuildRoad, EndTurn, RollDice
from hexcoach.engine.rules import apply, legal_actions, new_game, road_spot_ok
from hexcoach.engine.state import Phase


def ready_to_roll():
    rng = random.Random(0)
    state = new_game(seed=42)
    while state.phase != Phase.ROLL:
        state = apply(state, legal_actions(state)[0], rng)
    return state


def test_end_turn_passes_to_next_player_and_wraps_around():
    rng = random.Random(0)
    state = ready_to_roll()
    players = []
    for _ in range(4):
        players.append(state.current_player)
        state = apply(state, RollDice(), rng)
        assert EndTurn() in legal_actions(state)
        state = apply(state, EndTurn(), rng)
        assert state.phase == Phase.ROLL
    assert players == [0, 1, 2, 0]
    assert state.turn_number == 4


def road_moves(state):
    return [a for a in legal_actions(state) if isinstance(a, BuildRoad)]


def main_phase_with_road_30():
    state = new_game(seed=42)
    state.phase = Phase.MAIN
    state.edge_owner[30] = 0
    return state


def test_road_connects_through_an_empty_corner():
    assert road_spot_ok(main_phase_with_road_30(), player=0, edge=31)


def test_road_cannot_pass_through_an_opponents_building():
    state = main_phase_with_road_30()
    state.vertex_owner[25] = 1
    state.vertex_level[25] = 1
    assert not road_spot_ok(state, player=0, edge=31)


def test_road_can_start_from_your_own_building():
    state = new_game(seed=42)
    state.vertex_owner[25] = 0
    state.vertex_level[25] = 1
    assert road_spot_ok(state, player=0, edge=31)


def test_road_must_connect_to_something_of_yours():
    assert not road_spot_ok(main_phase_with_road_30(), player=0, edge=0)
    assert not road_spot_ok(main_phase_with_road_30(), player=1, edge=31)


def test_no_road_moves_without_wood_and_brick():
    state = main_phase_with_road_30()
    state.hands[0] = [0, 5, 5, 5, 5]
    assert road_moves(state) == []


def test_building_a_road_pays_the_bank_and_uses_a_piece():
    state = main_phase_with_road_30()
    state.hands[0] = [1, 1, 0, 0, 0]
    state.bank = [18, 18, 19, 19, 19]
    assert BuildRoad(31) in legal_actions(state)
    after = apply(state, BuildRoad(31), random.Random(0))
    assert after.edge_owner[31] == 0
    assert after.hands[0] == [0, 0, 0, 0, 0]
    assert after.bank == [19, 19, 19, 19, 19]
    assert after.pieces_left[0] == (14, 5, 4)


def test_no_road_moves_when_out_of_road_pieces():
    state = main_phase_with_road_30()
    state.hands[0] = [1, 1, 0, 0, 0]
    state.pieces_left[0] = (0, 5, 4)
    assert road_moves(state) == []
