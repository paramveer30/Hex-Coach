import random

from hexcoach.engine.actions import BuildCity, BuildSettlement
from hexcoach.engine.board import DESERT
from hexcoach.engine.geometry import VERTEX_HEXES
from hexcoach.engine.rules import apply, legal_actions, new_game, produce
from hexcoach.engine.state import Phase


def settlement_moves(state):
    return [a for a in legal_actions(state) if isinstance(a, BuildSettlement)]


def p0_with_two_roads_from_corner_9():
    # [9: P0 settlement] =road 14= (13) =road 20= (18)
    state = new_game(seed=42)
    state.phase = Phase.MAIN
    state.vertex_owner[9] = 0
    state.vertex_level[9] = 1
    state.edge_owner[14] = 0
    state.edge_owner[20] = 0
    state.hands[0] = [1, 1, 1, 1, 0]
    state.bank = [18, 18, 18, 18, 19]
    return state


def test_settlement_needs_two_roads_out():
    state = p0_with_two_roads_from_corner_9()
    assert settlement_moves(state) == [BuildSettlement(18)]


def test_settlement_must_touch_your_road():
    state = p0_with_two_roads_from_corner_9()
    state.edge_owner[20] = 1
    assert settlement_moves(state) == []


def test_settlement_needs_all_four_cards():
    state = p0_with_two_roads_from_corner_9()
    state.hands[0] = [1, 1, 1, 0, 5]
    assert settlement_moves(state) == []


def test_building_a_settlement():
    state = p0_with_two_roads_from_corner_9()
    after = apply(state, BuildSettlement(18), random.Random(0))
    assert after.vertex_owner[18] == 0
    assert after.vertex_level[18] == 1
    assert after.hands[0] == [0, 0, 0, 0, 0]
    assert after.bank == [19] * 5
    assert after.pieces_left[0] == (15, 4, 4)


def test_no_settlement_moves_when_out_of_pieces():
    state = p0_with_two_roads_from_corner_9()
    state.pieces_left[0] = (15, 0, 4)
    assert settlement_moves(state) == []


def test_city_upgrades_your_own_settlement_only():
    state = p0_with_two_roads_from_corner_9()
    state.vertex_owner[30] = 1
    state.vertex_level[30] = 1
    state.hands[0] = [0, 0, 0, 2, 3]
    cities = [a for a in legal_actions(state) if isinstance(a, BuildCity)]
    assert cities == [BuildCity(9)]


def test_building_a_city_returns_the_settlement_piece():
    state = p0_with_two_roads_from_corner_9()
    state.hands[0] = [0, 0, 0, 2, 3]
    state.bank = [19, 19, 19, 17, 16]
    state.pieces_left[0] = (13, 3, 4)
    after = apply(state, BuildCity(9), random.Random(0))
    assert after.vertex_level[9] == 2
    assert after.hands[0] == [0, 0, 0, 0, 0]
    assert after.bank == [19] * 5
    assert after.pieces_left[0] == (13, 4, 3)


def test_city_produces_two_cards():
    state = p0_with_two_roads_from_corner_9()
    state.hands[0] = [0, 0, 0, 2, 3]
    after = apply(state, BuildCity(9), random.Random(0))
    h = next(h for h in VERTEX_HEXES[9] if after.board.hex_resource[h] != DESERT)
    resource = after.board.hex_resource[h]
    before = after.hands[0][resource]
    produce(after, after.board.hex_number[h])
    assert after.hands[0][resource] - before >= 2
