"""Things that must be true after every move. Used by tests, not by the game loop."""

from hexcoach.engine.board import NUM_RESOURCES
from hexcoach.engine.geometry import (
    EDGE_VERTICES,
    NUM_EDGES,
    NUM_HEXES,
    NUM_VERTICES,
    VERTEX_NEIGHBORS,
)
from hexcoach.engine.longest_road import longest_road_length
from hexcoach.engine.state import GameState

BANK_START = 19
EMPTY = -1


def check_resources(state: GameState) -> None:
    for r in range(NUM_RESOURCES):
        total = state.bank[r] + sum(hand[r] for hand in state.hands)
        assert total == BANK_START, f"resource {r}: bank + hands = {total}, expected 19"
    for hand in state.hands:
        assert min(hand) >= 0, f"negative hand: {hand}"
    assert min(state.bank) >= 0, f"negative bank: {state.bank}"


def check_pieces(state: GameState) -> None:
    for p in range(state.num_players):
        roads_left, settlements_left, cities_left = state.pieces_left[p]
        roads = state.edge_owner.count(p)
        owned = [
            lvl for o, lvl in zip(state.vertex_owner, state.vertex_level, strict=True) if o == p
        ]
        assert roads + roads_left == 15, f"player {p}: {roads} roads + {roads_left} left"
        assert owned.count(1) + settlements_left == 5, f"player {p}: settlement count"
        assert owned.count(2) + cities_left == 4, f"player {p}: city count"
        assert min(roads_left, settlements_left, cities_left) >= 0, f"player {p}: negative pieces"


def check_distance_rule(state: GameState) -> None:
    for v in range(NUM_VERTICES):
        if state.vertex_owner[v] == EMPTY:
            continue
        assert state.vertex_level[v] in (1, 2), (
            f"vertex {v}: owned but level {state.vertex_level[v]}"
        )
        for n in VERTEX_NEIGHBORS[v]:
            assert state.vertex_owner[n] == EMPTY, f"buildings on neighboring vertices {v} and {n}"


def check_roads_connected(state: GameState) -> None:
    for p in range(state.num_players):
        roads = [e for e in range(NUM_EDGES) if state.edge_owner[e] == p]
        reached = {v for v in range(NUM_VERTICES) if state.vertex_owner[v] == p}
        connected: set[int] = set()
        changed = True
        while changed:
            changed = False
            for e in roads:
                if e not in connected and any(v in reached for v in EDGE_VERTICES[e]):
                    connected.add(e)
                    reached.update(EDGE_VERTICES[e])
                    changed = True
        loose = [e for e in roads if e not in connected]
        assert not loose, f"player {p}: roads {loose} not connected to their buildings"


def check_longest_road(state: GameState) -> None:
    for p in range(state.num_players):
        actual = longest_road_length(state.edge_owner, state.vertex_owner, p)
        assert state.longest_road_len[p] == actual, (
            f"player {p}: stored {state.longest_road_len[p]}, actual {actual}"
        )
    holder = state.longest_road_holder
    if holder != EMPTY:
        assert state.longest_road_len[holder] >= 5, f"holder {holder} has a road under 5"
        assert state.longest_road_len[holder] == max(state.longest_road_len), (
            f"holder {holder} is not longest"
        )


def check_robber(state: GameState) -> None:
    assert 0 <= state.robber_hex < NUM_HEXES, f"robber on hex {state.robber_hex}"


def assert_invariants(state: GameState) -> None:
    check_resources(state)
    check_pieces(state)
    check_distance_rule(state)
    check_roads_connected(state)
    check_longest_road(state)
    check_robber(state)
