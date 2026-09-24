import dataclasses
from collections import Counter

import pytest

from hexcoach.engine.board import (
    BRICK,
    DESERT,
    GENERIC_PORT,
    NUMBER_TOKENS,
    ORE,
    SHEEP,
    WHEAT,
    WOOD,
    generate_board,
    pips,
    reds_adjacent,
)
from hexcoach.engine.geometry import HEX_NEIGHBORS

SEEDS = range(300)


def test_same_seed_gives_same_board():
    assert generate_board(42) == generate_board(42)


def test_different_seeds_give_different_boards():
    boards = {generate_board(s) for s in range(20)}
    assert len(boards) == 20


def test_terrain_counts():
    for seed in SEEDS:
        counts = Counter(generate_board(seed).hex_resource)
        assert counts == {WOOD: 4, SHEEP: 4, WHEAT: 4, BRICK: 3, ORE: 3, DESERT: 1}


def test_tokens_are_the_standard_18_and_desert_has_none():
    for seed in SEEDS:
        board = generate_board(seed)
        assert board.hex_number[board.desert_hex] == 0
        assert board.hex_resource[board.desert_hex] == DESERT
        placed = sorted(n for n in board.hex_number if n != 0)
        assert placed == sorted(NUMBER_TOKENS)


def test_no_red_numbers_adjacent():
    for seed in SEEDS:
        numbers = generate_board(seed).hex_number
        for h, n in enumerate(numbers):
            if n in (6, 8):
                assert all(numbers[nb] not in (6, 8) for nb in HEX_NEIGHBORS[h])


def test_reds_adjacent_detects_a_bad_layout():
    numbers = [0] * 19
    a = 9
    b = HEX_NEIGHBORS[a][0]
    numbers[a], numbers[b] = 6, 8
    assert reds_adjacent(tuple(numbers))


def test_port_types_are_4_generic_and_one_of_each_resource():
    for seed in SEEDS:
        counts = Counter(generate_board(seed).port_type)
        assert counts == {GENERIC_PORT: 4, WOOD: 1, BRICK: 1, SHEEP: 1, WHEAT: 1, ORE: 1}


def test_board_is_immutable():
    board = generate_board(0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        board.desert_hex = 3


def test_pips_match_dice_odds():
    assert [pips(n) for n in range(2, 13)] == [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    assert pips(0) == 0
