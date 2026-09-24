"""Seeded board generation: terrain, number tokens, and port types."""

import random
from dataclasses import dataclass

from hexcoach.engine.geometry import HEX_NEIGHBORS, NUM_HEXES

WOOD, BRICK, SHEEP, WHEAT, ORE = range(5)
NUM_RESOURCES = 5
DESERT = -1
GENERIC_PORT = -1

TERRAIN = [WOOD] * 4 + [SHEEP] * 4 + [WHEAT] * 4 + [BRICK] * 3 + [ORE] * 3 + [DESERT]
NUMBER_TOKENS = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
PORT_TYPES = [GENERIC_PORT] * 4 + [WOOD, BRICK, SHEEP, WHEAT, ORE]
RED_NUMBERS = (6, 8)


@dataclass(frozen=True, slots=True)
class Board:
    hex_resource: tuple[int, ...]  # resource per hex, DESERT for the desert
    hex_number: tuple[int, ...]  # token per hex, 0 for the desert
    port_type: tuple[int, ...]  # per port spot in geometry.PORT_EDGES order
    desert_hex: int


def reds_adjacent(hex_number: tuple[int, ...]) -> bool:
    for h, n in enumerate(hex_number):
        if n in RED_NUMBERS and any(hex_number[nb] in RED_NUMBERS for nb in HEX_NEIGHBORS[h]):
            return True
    return False


def generate_board(seed: int) -> Board:
    rng = random.Random(seed)

    terrain = TERRAIN[:]
    rng.shuffle(terrain)
    desert_hex = terrain.index(DESERT)

    tokens = NUMBER_TOKENS[:]
    while True:
        rng.shuffle(tokens)
        it = iter(tokens)
        numbers = tuple(0 if h == desert_hex else next(it) for h in range(NUM_HEXES))
        if not reds_adjacent(numbers):
            break

    ports = PORT_TYPES[:]
    rng.shuffle(ports)

    return Board(
        hex_resource=tuple(terrain),
        hex_number=numbers,
        port_type=tuple(ports),
        desert_hex=desert_hex,
    )


def pips(number: int) -> int:
    # dice combinations out of 36 that roll this number; the desert's 0 has none
    return 0 if number == 0 else 6 - abs(7 - number)
