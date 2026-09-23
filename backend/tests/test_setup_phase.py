import random

from hexcoach.engine.actions import PlaceSetupSettlement
from hexcoach.engine.board import DESERT
from hexcoach.engine.geometry import VERTEX_EDGES, VERTEX_HEXES, VERTEX_NEIGHBORS
from hexcoach.engine.rules import EMPTY, apply, legal_actions, new_game, setup_order
from hexcoach.engine.state import Phase


def test_new_game_starts_empty_in_setup():
    state = new_game(seed=42)
    assert state.phase == Phase.SETUP_SETTLEMENT
    assert state.current_player == 0
    assert all(owner == EMPTY for owner in state.vertex_owner)
    assert all(owner == EMPTY for owner in state.edge_owner)
    assert state.hands == [[0] * 5] * 3
    assert state.bank == [19] * 5
    assert state.robber_hex == state.board.desert_hex


def test_new_game_hands_are_separate_lists():
    state = new_game(seed=42)
    state.hands[0][0] = 5
    assert state.hands[1][0] == 0


def play_setup(seed=42, pick=0):
    rng = random.Random(0)
    state = new_game(seed)
    history = []
    while state.phase in (Phase.SETUP_SETTLEMENT, Phase.SETUP_ROAD):
        action = legal_actions(state)[pick]
        history.append((state.current_player, action))
        state = apply(state, action, rng)
    return state, history


def test_setup_follows_snake_order():
    _, history = play_setup()
    settlers = [p for p, a in history if isinstance(a, PlaceSetupSettlement)]
    assert settlers == [0, 1, 2, 2, 1, 0]
    assert setup_order(4) == [0, 1, 2, 3, 3, 2, 1, 0]


def test_setup_ends_with_player_0_rolling():
    state, _ = play_setup()
    assert state.phase == Phase.ROLL
    assert state.current_player == 0


def test_each_player_ends_setup_with_2_settlements_and_2_roads():
    state, _ = play_setup()
    for p in range(3):
        assert state.vertex_owner.count(p) == 2
        assert state.edge_owner.count(p) == 2
        assert state.pieces_left[p] == (13, 3, 4)


def test_setup_road_must_touch_the_settlement_just_placed():
    state = apply(new_game(42), PlaceSetupSettlement(22), random.Random(0))
    roads = legal_actions(state)
    assert roads
    for action in roads:
        assert action.edge in VERTEX_EDGES[22]


def test_first_settlement_gives_no_cards():
    state = apply(new_game(42), PlaceSetupSettlement(22), random.Random(0))
    assert state.hands[0] == [0, 0, 0, 0, 0]


def test_second_settlement_gives_one_card_per_touching_hex():
    state, history = play_setup()
    for p in range(3):
        second = [a.vertex for q, a in history if q == p and isinstance(a, PlaceSetupSettlement)][1]
        expected = [0] * 5
        for h in VERTEX_HEXES[second]:
            if state.board.hex_resource[h] != DESERT:
                expected[state.board.hex_resource[h]] += 1
        assert state.hands[p] == expected


def test_cards_come_out_of_the_bank():
    state, _ = play_setup()
    for r in range(5):
        assert state.bank[r] + sum(hand[r] for hand in state.hands) == 19


def test_distance_rule_holds_during_setup():
    for pick in (0, -1):
        state, _ = play_setup(pick=pick)
        owned = [v for v in range(54) if state.vertex_owner[v] != EMPTY]
        for v in owned:
            assert all(state.vertex_owner[n] == EMPTY for n in VERTEX_NEIGHBORS[v])


def test_apply_never_changes_its_input():
    state = new_game(42)
    before = state.clone()
    apply(state, PlaceSetupSettlement(22), random.Random(0))
    assert state == before
