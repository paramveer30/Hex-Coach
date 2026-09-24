"""Rule-based bot: score spots by pips, new resources, and ports, then follow fixed priorities."""

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
)
from hexcoach.engine.board import DESERT, GENERIC_PORT, pips
from hexcoach.engine.geometry import (
    EDGE_VERTICES,
    HEX_VERTICES,
    NUM_EDGES,
    NUM_VERTICES,
    PORT_VERTICES,
    VERTEX_HEXES,
    VERTEX_NEIGHBORS,
)
from hexcoach.engine.rules import (
    CITY_COST,
    ROAD_COST,
    SETTLEMENT_COST,
    can_afford,
    legal_actions,
    player_to_move,
    road_spot_ok,
    settlement_spot_ok,
    touches_own_road,
    trade_rate,
    victory_points,
)
from hexcoach.engine.state import GameState, Phase

NEW_RESOURCE_WEIGHT = 1.5
GENERIC_PORT_BONUS = 1.0
SPECIFIC_PORT_BONUS = 2.0

VERTEX_PORT = {v: port for port, pair in enumerate(PORT_VERTICES) for v in pair}


def produced_resources(state: GameState, player: int) -> set[int]:
    produced = set()
    for v in range(NUM_VERTICES):
        if state.vertex_owner[v] == player:
            produced |= {state.board.hex_resource[h] for h in VERTEX_HEXES[v]}
    produced.discard(DESERT)
    return produced


def vertex_pips(state: GameState, v: int) -> int:
    return sum(pips(state.board.hex_number[h]) for h in VERTEX_HEXES[v])


def vertex_score(state: GameState, v: int, produced: set[int]) -> float:
    here = {state.board.hex_resource[h] for h in VERTEX_HEXES[v]} - {DESERT}
    score = vertex_pips(state, v) + NEW_RESOURCE_WEIGHT * len(here - produced)
    port = VERTEX_PORT.get(v)
    if port is not None:
        kind = state.board.port_type[port]
        if kind == GENERIC_PORT:
            score += GENERIC_PORT_BONUS
        elif kind in produced | here:
            score += SPECIFIC_PORT_BONUS
    return score


def road_target(state: GameState, edge: int, produced: set[int]) -> float | None:
    # best open settlement spot at most 2 edges away once this road is built
    best = None
    for end in EDGE_VERTICES[edge]:
        for v in (end, *VERTEX_NEIGHBORS[end]):
            if settlement_spot_ok(state.vertex_owner, v):
                score = vertex_score(state, v, produced)
                best = score if best is None else max(best, score)
    return best


def leader(state: GameState, me: int) -> int:
    others = [p for p in range(state.num_players) if p != me]
    return max(others, key=lambda p: (victory_points(state, p), sum(state.hands[p]), -p))


class HeuristicBot:
    def choose(self, state: GameState, rng: random.Random) -> Action:
        actions = legal_actions(state)
        if len(actions) == 1:
            return actions[0]
        me = player_to_move(state)
        produced = produced_resources(state, me)

        if state.phase == Phase.SETUP_SETTLEMENT:
            return max(actions, key=lambda a: vertex_score(state, a.vertex, produced))
        if state.phase == Phase.SETUP_ROAD:
            return max(actions, key=lambda a: road_target(state, a.edge, produced) or 0)
        if state.phase == Phase.DISCARD:
            return self.discard(state, me, actions)
        if state.phase == Phase.MOVE_ROBBER:
            return self.move_robber(state, me, actions)
        if state.phase == Phase.STEAL:
            return self.steal(state, me, actions)
        return self.main_phase(state, me, actions, produced)

    def main_phase(self, state, me, actions, produced) -> Action:
        cities = [a for a in actions if isinstance(a, BuildCity)]
        if cities:
            return max(cities, key=lambda a: vertex_pips(state, a.vertex))
        settlements = [a for a in actions if isinstance(a, BuildSettlement)]
        if settlements:
            return max(settlements, key=lambda a: vertex_score(state, a.vertex, produced))
        roads = [
            (road_target(state, a.edge, produced), a) for a in actions if isinstance(a, BuildRoad)
        ]
        roads = [(score, a) for score, a in roads if score is not None]
        if roads:
            return max(roads, key=lambda pair: pair[0])[1]
        trade = self.completing_trade(state, me, actions, produced)
        return trade if trade is not None else EndTurn()

    def completing_trade(self, state, me, actions, produced) -> Action | None:
        roads_left, settlements_left, cities_left = state.pieces_left[me]
        has_settlement = any(
            state.vertex_owner[v] == me and state.vertex_level[v] == 1 for v in range(NUM_VERTICES)
        )
        has_settlement_spot = any(
            settlement_spot_ok(state.vertex_owner, v) and touches_own_road(state, me, v)
            for v in range(NUM_VERTICES)
        )
        has_road_target = any(
            road_spot_ok(state, me, e) and road_target(state, e, produced) is not None
            for e in range(NUM_EDGES)
        )
        goals = []
        if cities_left > 0 and has_settlement:
            goals.append(CITY_COST)
        if settlements_left > 0 and has_settlement_spot:
            goals.append(SETTLEMENT_COST)
        if roads_left > 0 and has_road_target:
            goals.append(ROAD_COST)

        trades = [a for a in actions if isinstance(a, BankTrade)]
        for cost in goals:
            for trade in trades:
                hand = state.hands[me][:]
                hand[trade.give] -= trade_rate(state, me, trade.give)
                hand[trade.get] += 1
                if can_afford(hand, cost):
                    return trade
        return None

    def discard(self, state, me, actions) -> Action:
        _, settlements_left, cities_left = state.pieces_left[me]
        has_settlement = any(
            state.vertex_owner[v] == me and state.vertex_level[v] == 1 for v in range(NUM_VERTICES)
        )
        if cities_left > 0 and has_settlement:
            goal = CITY_COST
        elif settlements_left > 0:
            goal = SETTLEMENT_COST
        else:
            goal = ROAD_COST
        hand = state.hands[me]

        def kept_toward_goal(d: Discard) -> int:
            return sum(
                min(have - gone, need)
                for have, gone, need in zip(hand, d.counts, goal, strict=True)
            )

        return max(actions, key=kept_toward_goal)

    def move_robber(self, state, me, actions) -> Action:
        target = leader(state, me)

        def value(a: MoveRobber) -> tuple:
            owners = [(state.vertex_owner[v], state.vertex_level[v]) for v in HEX_VERTICES[a.hex]]
            mine = any(owner == me for owner, _ in owners)
            hex_pips = pips(state.board.hex_number[a.hex])
            on_leader = sum(level for owner, level in owners if owner == target) * hex_pips
            on_others = sum(level for owner, level in owners if owner not in (-1, me)) * hex_pips
            return (not mine, on_leader, on_others)

        return max(actions, key=value)

    def steal(self, state, me, actions) -> Action:
        target = leader(state, me)
        return max(
            actions,
            key=lambda a: (
                a.victim == target,
                victory_points(state, a.victim),
                sum(state.hands[a.victim]),
            ),
        )
