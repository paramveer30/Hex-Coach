import random
from collections import Counter

from hexcoach.engine.actions import RollDice
from hexcoach.engine.board import DESERT, WHEAT
from hexcoach.engine.geometry import HEX_VERTICES
from hexcoach.engine.rules import apply, legal_actions, new_game, produce
from hexcoach.engine.state import Phase


def game_with_building(level):
    state = new_game(seed=42)
    hex_id = next(h for h in range(19) if state.board.hex_resource[h] != DESERT)
    corner = HEX_VERTICES[hex_id][0]
    state.vertex_owner[corner] = 1
    state.vertex_level[corner] = level
    return state, hex_id


def test_settlement_gets_1_card():
    state, h = game_with_building(level=1)
    resource = state.board.hex_resource[h]
    produce(state, state.board.hex_number[h])
    assert state.hands[1][resource] == 1
    assert state.bank[resource] == 18


def test_city_gets_2_cards():
    state, h = game_with_building(level=2)
    resource = state.board.hex_resource[h]
    produce(state, state.board.hex_number[h])
    assert state.hands[1][resource] == 2


def test_robber_blocks_production():
    state, h = game_with_building(level=1)
    state.robber_hex = h
    produce(state, state.board.hex_number[h])
    assert state.hands[1] == [0, 0, 0, 0, 0]


def test_other_numbers_produce_nothing():
    state, h = game_with_building(level=1)
    other = 7 if state.board.hex_number[h] != 7 else 2
    produce(state, other)
    assert state.hands[1] == [0, 0, 0, 0, 0]


def ready_to_roll():
    rng = random.Random(0)
    state = new_game(seed=42)
    while state.phase != Phase.ROLL:
        state = apply(state, legal_actions(state)[0], rng)
    return state


def test_same_rng_seed_gives_same_roll_and_moves_to_main():
    state = ready_to_roll()
    a = apply(state, RollDice(), random.Random(7))
    b = apply(state, RollDice(), random.Random(7))
    assert a.last_roll == b.last_roll
    assert a == b
    assert a.phase == Phase.MAIN


def test_rolls_follow_two_dice_odds():
    state = ready_to_roll()
    counts = Counter(apply(state, RollDice(), random.Random(i)).last_roll for i in range(3600))
    assert set(counts) == set(range(2, 13))
    assert counts.most_common(1)[0][0] == 7
    assert counts[2] < counts[7] / 3


def wheat_hex_with(buildings, bank_wheat):
    # buildings: list of (player, level) placed on opposite corners of one wheat hex
    state = new_game(seed=42)
    h = next(h for h in range(19) if state.board.hex_resource[h] == WHEAT)
    for corner, (player, level) in zip((0, 3), buildings, strict=False):
        v = HEX_VERTICES[h][corner]
        state.vertex_owner[v] = player
        state.vertex_level[v] = level
    state.bank[WHEAT] = bank_wheat
    produce(state, state.board.hex_number[h])
    return [hand[WHEAT] for hand in state.hands], state.bank[WHEAT]


def test_bank_pays_everyone_when_it_can():
    assert wheat_hex_with([(0, 2), (1, 1)], bank_wheat=3) == ([2, 1, 0], 0)


def test_bank_short_and_two_players_owed_pays_nobody():
    assert wheat_hex_with([(0, 2), (1, 2)], bank_wheat=3) == ([0, 0, 0], 3)


def test_bank_short_and_one_player_owed_gets_whats_left():
    assert wheat_hex_with([(0, 2)], bank_wheat=1) == ([1, 0, 0], 0)
