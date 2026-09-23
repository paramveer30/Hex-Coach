"""The rules: legal moves, applying moves, and scoring."""

import random

from hexcoach.engine.actions import (
    Action,
    BankTrade,
    BuildCity,
    BuildRoad,
    BuildSettlement,
    EndTurn,
    PlaceSetupRoad,
    PlaceSetupSettlement,
    RollDice,
)
from hexcoach.engine.board import DESERT, GENERIC_PORT, NUM_RESOURCES, generate_board
from hexcoach.engine.geometry import (
    EDGE_VERTICES,
    HEX_VERTICES,
    NUM_EDGES,
    NUM_HEXES,
    NUM_VERTICES,
    PORT_VERTICES,
    VERTEX_EDGES,
    VERTEX_HEXES,
    VERTEX_NEIGHBORS,
)
from hexcoach.engine.state import GameState, Phase

EMPTY = -1
BANK_START = 19
PIECES_START = (15, 5, 4)  # roads, settlements, cities

# wood, brick, sheep, wheat, ore
ROAD_COST = (1, 1, 0, 0, 0)
SETTLEMENT_COST = (1, 1, 1, 1, 0)
CITY_COST = (0, 0, 0, 2, 3)


def can_afford(hand: list[int], cost: tuple[int, ...]) -> bool:
    return all(have >= need for have, need in zip(hand, cost, strict=True))


def pay(s: GameState, player: int, cost: tuple[int, ...]) -> None:
    for r, amount in enumerate(cost):
        s.hands[player][r] -= amount
        s.bank[r] += amount


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


def touches_own_road(state: GameState, player: int, vertex: int) -> bool:
    return any(state.edge_owner[e] == player for e in VERTEX_EDGES[vertex])


def road_spot_ok(state: GameState, player: int, edge: int) -> bool:
    if state.edge_owner[edge] != EMPTY:
        return False
    for v in EDGE_VERTICES[edge]:
        owner = state.vertex_owner[v]
        if owner == player:
            return True
        if owner == EMPTY and any(state.edge_owner[e] == player for e in VERTEX_EDGES[v]):
            return True
    return False


def trade_rate(state: GameState, player: int, resource: int) -> int:
    rate = 4
    for port, (a, b) in enumerate(PORT_VERTICES):
        if state.vertex_owner[a] != player and state.vertex_owner[b] != player:
            continue
        kind = state.board.port_type[port]
        if kind == resource:
            return 2
        if kind == GENERIC_PORT:
            rate = 3
    return rate


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
    if state.phase == Phase.MAIN:
        return main_actions(state)
    raise NotImplementedError(state.phase)


def main_actions(state: GameState) -> list[Action]:
    p = state.current_player
    hand = state.hands[p]
    roads_left, settlements_left, cities_left = state.pieces_left[p]
    actions: list[Action] = [EndTurn()]
    if roads_left > 0 and can_afford(hand, ROAD_COST):
        actions += [BuildRoad(e) for e in range(NUM_EDGES) if road_spot_ok(state, p, e)]
    if settlements_left > 0 and can_afford(hand, SETTLEMENT_COST):
        actions += [
            BuildSettlement(v)
            for v in range(NUM_VERTICES)
            if settlement_spot_ok(state.vertex_owner, v) and touches_own_road(state, p, v)
        ]
    if cities_left > 0 and can_afford(hand, CITY_COST):
        actions += [
            BuildCity(v)
            for v in range(NUM_VERTICES)
            if state.vertex_owner[v] == p and state.vertex_level[v] == 1
        ]
    for give in range(NUM_RESOURCES):
        if hand[give] < trade_rate(state, p, give):
            continue
        actions += [
            BankTrade(give, get)
            for get in range(NUM_RESOURCES)
            if get != give and state.bank[get] > 0
        ]
    return actions


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

    if isinstance(action, BuildRoad):
        pay(s, p, ROAD_COST)
        s.edge_owner[action.edge] = p
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads - 1, settlements, cities)
        return s

    if isinstance(action, BuildSettlement):
        pay(s, p, SETTLEMENT_COST)
        s.vertex_owner[action.vertex] = p
        s.vertex_level[action.vertex] = 1
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads, settlements - 1, cities)
        return s

    if isinstance(action, BuildCity):
        pay(s, p, CITY_COST)
        s.vertex_level[action.vertex] = 2
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads, settlements + 1, cities - 1)
        return s

    if isinstance(action, BankTrade):
        rate = trade_rate(s, p, action.give)
        s.hands[p][action.give] -= rate
        s.bank[action.give] += rate
        s.hands[p][action.get] += 1
        s.bank[action.get] -= 1
        return s

    if isinstance(action, EndTurn):
        s.current_player = (p + 1) % s.num_players
        s.turn_number += 1
        s.phase = Phase.ROLL
        return s

    raise NotImplementedError(type(action).__name__)
