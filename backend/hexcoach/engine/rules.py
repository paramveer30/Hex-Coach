"""The rules: legal moves, applying moves, and scoring."""

import random

from hexcoach.engine.actions import Action, PlaceSetupRoad, PlaceSetupSettlement, RollDice
from hexcoach.engine.board import DESERT, NUM_RESOURCES, generate_board
from hexcoach.engine.geometry import (
    HEX_VERTICES,
    NUM_EDGES,
    NUM_HEXES,
    NUM_VERTICES,
    VERTEX_EDGES,
    VERTEX_HEXES,
    VERTEX_NEIGHBORS,
)
from hexcoach.engine.state import GameState, Phase

EMPTY = -1
BANK_START = 19
PIECES_START = (15, 5, 4)  # roads, settlements, cities


def setup_order(num_players: int) -> list[int]:
    forward = list(range(num_players))
    return forward + forward[::-1]


def new_game(seed: int, num_players: int = 3) -> GameState:
    board = generate_board(seed)
    return GameState(
        board=board,
        robber_hex=board.desert_hex,
        vertex_owner=[EMPTY] * NUM_VERTICES,
        vertex_level=[0] * NUM_VERTICES,
        edge_owner=[EMPTY] * NUM_EDGES,
        hands=[[0] * NUM_RESOURCES for _ in range(num_players)],
        bank=[BANK_START] * NUM_RESOURCES,
        pieces_left=[PIECES_START] * num_players,
        longest_road_holder=EMPTY,
        longest_road_len=[0] * num_players,
        current_player=0,
        phase=Phase.SETUP_SETTLEMENT,
        setup_step=0,
        setup_vertex=EMPTY,
        pending_discards=[],
        turn_number=0,
        last_roll=None,
        winner=None,
    )


def settlement_spot_ok(vertex_owner: list[int], vertex: int) -> bool:
    if vertex_owner[vertex] != EMPTY:
        return False
    for neighbor in VERTEX_NEIGHBORS[vertex]:
        if vertex_owner[neighbor] != EMPTY:
            return False
    return True


def produce(s: GameState, roll: int) -> None:
    owed = [[0] * NUM_RESOURCES for _ in range(s.num_players)]
    for h in range(NUM_HEXES):
        if s.board.hex_number[h] != roll or h == s.robber_hex:
            continue
        resource = s.board.hex_resource[h]
        for v in HEX_VERTICES[h]:
            if s.vertex_owner[v] != EMPTY:
                owed[s.vertex_owner[v]][resource] += s.vertex_level[v]

    for r in range(NUM_RESOURCES):
        total = sum(owed[p][r] for p in range(s.num_players))
        if total > s.bank[r]:
            continue
        for p in range(s.num_players):
            s.hands[p][r] += owed[p][r]
        s.bank[r] -= total


def legal_actions(state: GameState) -> list[Action]:
    if state.phase == Phase.SETUP_SETTLEMENT:
        return [
            PlaceSetupSettlement(v)
            for v in range(NUM_VERTICES)
            if settlement_spot_ok(state.vertex_owner, v)
        ]
    if state.phase == Phase.SETUP_ROAD:
        return [
            PlaceSetupRoad(e)
            for e in VERTEX_EDGES[state.setup_vertex]
            if state.edge_owner[e] == EMPTY
        ]
    if state.phase == Phase.ROLL:
        return [RollDice()]
    raise NotImplementedError(state.phase)


def apply(state: GameState, action: Action, rng: random.Random) -> GameState:
    s = state.clone()
    p = s.current_player

    if isinstance(action, PlaceSetupSettlement):
        v = action.vertex
        s.vertex_owner[v] = p
        s.vertex_level[v] = 1
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads, settlements - 1, cities)
        s.setup_vertex = v
        if s.setup_step >= s.num_players:
            for h in VERTEX_HEXES[v]:
                resource = s.board.hex_resource[h]
                if resource != DESERT:
                    s.hands[p][resource] += 1
                    s.bank[resource] -= 1
        s.phase = Phase.SETUP_ROAD
        return s

    if isinstance(action, PlaceSetupRoad):
        s.edge_owner[action.edge] = p
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads - 1, settlements, cities)
        s.setup_vertex = EMPTY
        s.setup_step += 1
        order = setup_order(s.num_players)
        if s.setup_step < len(order):
            s.current_player = order[s.setup_step]
            s.phase = Phase.SETUP_SETTLEMENT
        else:
            s.current_player = 0
            s.phase = Phase.ROLL
        return s

    if isinstance(action, RollDice):
        roll = rng.randint(1, 6) + rng.randint(1, 6)
        s.last_roll = roll
        if roll != 7:
            produce(s, roll)
        s.phase = Phase.MAIN
        return s

    raise NotImplementedError(type(action).__name__)
