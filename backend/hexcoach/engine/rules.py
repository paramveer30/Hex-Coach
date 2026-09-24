"""The rules: legal moves, applying moves, and scoring."""

import random

from hexcoach.engine.actions import (
    Action,
    BankTrade,
    BuildCity,
    BuildRoad,
    BuildSettlement,
    Discard,
    EndTurn,
    MoveRobber,
    PlaceSetupRoad,
    PlaceSetupSettlement,
    RollDice,
    Steal,
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
from hexcoach.engine.longest_road import longest_road_length
from hexcoach.engine.state import GameState, Phase

EMPTY = -1
BANK_START = 19
PIECES_START = (15, 5, 4)  # roads, settlements, cities
WINNING_VP = 10
TURN_CAP = 400
DISCARD_LIMIT = 7
MAX_DISCARD_CANDIDATES = 5
LONGEST_ROAD_VP = 2
LONGEST_ROAD_MIN = 5

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
        if total <= s.bank[r]:
            for p in range(s.num_players):
                s.hands[p][r] += owed[p][r]
            s.bank[r] -= total
            continue
        owed_players = [p for p in range(s.num_players) if owed[p][r] > 0]
        if len(owed_players) == 1:
            s.hands[owed_players[0]][r] += s.bank[r]
            s.bank[r] = 0


def victory_points(state: GameState, player: int) -> int:
    vp = sum(
        level
        for owner, level in zip(state.vertex_owner, state.vertex_level, strict=True)
        if owner == player
    )
    if state.longest_road_holder == player:
        vp += LONGEST_ROAD_VP
    return vp


def is_terminal(state: GameState) -> bool:
    return state.phase == Phase.GAME_OVER


def winner(state: GameState) -> int | None:
    return state.winner


def update_longest_road(s: GameState) -> None:
    lengths = [longest_road_length(s.edge_owner, s.vertex_owner, p) for p in range(s.num_players)]
    s.longest_road_len = lengths
    best = max(lengths)
    holder = s.longest_road_holder
    if best < LONGEST_ROAD_MIN:
        s.longest_road_holder = EMPTY
    elif holder != EMPTY and lengths[holder] == best:
        pass
    elif lengths.count(best) == 1:
        s.longest_road_holder = lengths.index(best)
    else:
        s.longest_road_holder = EMPTY


def check_win(s: GameState, player: int) -> None:
    if victory_points(s, player) >= WINNING_VP:
        s.winner = player
        s.phase = Phase.GAME_OVER


def end_by_turn_cap(s: GameState) -> None:
    vps = [victory_points(s, p) for p in range(s.num_players)]
    best = max(vps)
    leaders = [p for p, vp in enumerate(vps) if vp == best]
    s.winner = leaders[0] if len(leaders) == 1 else None
    s.phase = Phase.GAME_OVER


def player_to_move(state: GameState) -> int:
    if state.phase == Phase.DISCARD:
        return state.pending_discards[0]
    return state.current_player


def discard_candidates(hand: list[int]) -> list[Discard]:
    # one candidate per resource we'd most like to keep: discard from the
    # largest piles first, touching the protected resource only if we must
    need = sum(hand) // 2
    candidates = []
    for protect in range(NUM_RESOURCES):
        left = hand[:]
        counts = [0] * NUM_RESOURCES
        for _ in range(need):
            r = max(range(NUM_RESOURCES), key=lambda i: (left[i] > 0, i != protect, left[i]))
            left[r] -= 1
            counts[r] += 1
        discard = Discard(tuple(counts))
        if discard not in candidates:
            candidates.append(discard)
    return candidates[:MAX_DISCARD_CANDIDATES]


def steal_victims(state: GameState, hex_id: int) -> list[int]:
    roller = state.current_player
    victims = set()
    for v in HEX_VERTICES[hex_id]:
        owner = state.vertex_owner[v]
        if owner not in (EMPTY, roller) and sum(state.hands[owner]) > 0:
            victims.add(owner)
    return sorted(victims)


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
    if state.phase == Phase.DISCARD:
        return discard_candidates(state.hands[player_to_move(state)])
    if state.phase == Phase.MOVE_ROBBER:
        return [MoveRobber(h) for h in range(NUM_HEXES) if h != state.robber_hex]
    if state.phase == Phase.STEAL:
        return [Steal(v) for v in steal_victims(state, state.robber_hex)]
    if state.phase == Phase.MAIN:
        return main_actions(state)
    if state.phase == Phase.GAME_OVER:
        return []
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
        s.pending_discards = [q for q in range(s.num_players) if sum(s.hands[q]) > DISCARD_LIMIT]
        s.phase = Phase.DISCARD if s.pending_discards else Phase.MOVE_ROBBER
        return s

    if isinstance(action, Discard):
        q = s.pending_discards.pop(0)
        for r, n in enumerate(action.counts):
            s.hands[q][r] -= n
            s.bank[r] += n
        if not s.pending_discards:
            s.phase = Phase.MOVE_ROBBER
        return s

    if isinstance(action, MoveRobber):
        s.robber_hex = action.hex
        s.phase = Phase.STEAL if steal_victims(s, action.hex) else Phase.MAIN
        return s

    if isinstance(action, Steal):
        victim_hand = s.hands[action.victim]
        pick = rng.randrange(sum(victim_hand))
        for r in range(NUM_RESOURCES):
            if pick < victim_hand[r]:
                break
            pick -= victim_hand[r]
        victim_hand[r] -= 1
        s.hands[p][r] += 1
        s.phase = Phase.MAIN
        return s

    if isinstance(action, BuildRoad):
        pay(s, p, ROAD_COST)
        s.edge_owner[action.edge] = p
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads - 1, settlements, cities)
        update_longest_road(s)
        check_win(s, p)
        return s

    if isinstance(action, BuildSettlement):
        pay(s, p, SETTLEMENT_COST)
        s.vertex_owner[action.vertex] = p
        s.vertex_level[action.vertex] = 1
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads, settlements - 1, cities)
        update_longest_road(s)
        check_win(s, p)
        return s

    if isinstance(action, BuildCity):
        pay(s, p, CITY_COST)
        s.vertex_level[action.vertex] = 2
        roads, settlements, cities = s.pieces_left[p]
        s.pieces_left[p] = (roads, settlements + 1, cities - 1)
        check_win(s, p)
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
        # longest road can change hands on someone else's turn; you win when your turn starts
        check_win(s, s.current_player)
        if s.phase != Phase.GAME_OVER and s.turn_number >= TURN_CAP:
            end_by_turn_cap(s)
        return s

    raise NotImplementedError(type(action).__name__)
