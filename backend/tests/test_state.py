import dataclasses
import timeit

import pytest

from hexcoach.engine.actions import BankTrade, BuildRoad, Discard, EndTurn, RollDice
from hexcoach.engine.board import generate_board
from hexcoach.engine.geometry import NUM_EDGES, NUM_VERTICES
from hexcoach.engine.state import GameState, Phase


def blank_state(num_players=3):
    board = generate_board(0)
    return GameState(
        board=board,
        robber_hex=board.desert_hex,
        vertex_owner=[-1] * NUM_VERTICES,
        vertex_level=[0] * NUM_VERTICES,
        edge_owner=[-1] * NUM_EDGES,
        hands=[[0] * 5 for _ in range(num_players)],
        bank=[19] * 5,
        pieces_left=[(15, 5, 4)] * num_players,
        longest_road_holder=-1,
        longest_road_len=[0] * num_players,
        current_player=0,
        phase=Phase.SETUP_SETTLEMENT,
        setup_step=0,
        setup_vertex=-1,
        pending_discards=[],
        turn_number=0,
        last_roll=None,
        winner=None,
    )


def test_clone_is_equal_but_not_the_same_object():
    state = blank_state()
    copy = state.clone()
    assert copy == state
    assert copy is not state


def test_changing_the_clone_never_touches_the_original():
    state = blank_state()
    copy = state.clone()
    copy.vertex_owner[10] = 1
    copy.edge_owner[5] = 2
    copy.hands[0][3] = 4
    copy.bank[3] = 15
    copy.pieces_left[1] = (14, 5, 4)
    copy.pending_discards.append(2)
    copy.current_player = 2
    assert state == blank_state()


def test_clone_shares_the_immutable_board():
    state = blank_state()
    assert state.clone().board is state.board


def test_clone_covers_every_field():
    # if a field is added to GameState but forgotten in clone(), this catches it
    state = blank_state()
    for field in dataclasses.fields(GameState):
        assert getattr(state.clone(), field.name) == getattr(state, field.name)


def test_actions_compare_and_hash_by_value():
    assert BuildRoad(5) == BuildRoad(5)
    assert BuildRoad(5) != BuildRoad(6)
    assert len({BuildRoad(5), BuildRoad(5), RollDice(), RollDice(), EndTurn()}) == 3
    visits = {BankTrade(give=0, get=4): 10}
    assert visits[BankTrade(0, 4)] == 10


def test_actions_are_immutable():
    action = Discard((1, 0, 2, 0, 0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        action.counts = (0, 0, 0, 0, 0)


def test_clone_is_fast():
    state = blank_state()
    per_clone = timeit.timeit(state.clone, number=10_000) / 10_000
    assert per_clone < 20e-6
