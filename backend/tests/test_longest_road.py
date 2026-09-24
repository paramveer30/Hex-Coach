import random

from hexcoach.engine.actions import BuildSettlement
from hexcoach.engine.geometry import (
    COASTAL_EDGES,
    EDGE_VERTICES,
    NUM_EDGES,
    NUM_VERTICES,
    VERTEX_EDGES,
)
from hexcoach.engine.longest_road import longest_road_length
from hexcoach.engine.rules import apply, new_game, update_longest_road, victory_points
from hexcoach.engine.state import Phase

# coastal chain through corners 21-16-11-7-3-0-4-1
CHAIN = [23, 18, 10, 6, 0, 1, 2]
# the 6 edges around the center hex, and a spoke leaving its corner 24
RING = [36, 44, 43, 35, 27, 28]
SPOKE = 29


def length(edges, buildings=()):
    edge_owner = [-1] * NUM_EDGES
    for e in edges:
        edge_owner[e] = 0
    vertex_owner = [-1] * NUM_VERTICES
    for vertex, player in buildings:
        vertex_owner[vertex] = player
    return longest_road_length(edge_owner, vertex_owner, 0)


def test_no_roads_is_0():
    assert length([]) == 0


def test_straight_chains():
    assert length(CHAIN[:1]) == 1
    assert length(CHAIN[:5]) == 5
    assert length(CHAIN) == 7


def test_branch_does_not_add_up():
    # a Y at corner 7: arms 7-11-16-21 (3), 7-3-0 (2), 7-12 (1) = 6 roads,
    # but a single trace can use only two arms: 3 + 2 = 5
    assert EDGE_VERTICES[11] == (7, 12)
    assert length(CHAIN[:5] + [11]) == 5


def test_loop_counts_every_edge_once():
    assert length(RING) == 6


def test_loop_plus_a_tail():
    # go around the whole ring and leave by the spoke at corner 24
    assert 24 in EDGE_VERTICES[SPOKE]
    assert length(RING + [SPOKE]) == 7


def test_opponent_building_breaks_the_road():
    # opponent on corner 7 splits 21-16-11-7 | 7-3-0-4 into 3 and 3
    assert length(CHAIN[:6], buildings=[(7, 1)]) == 3


def test_your_own_building_does_not_break_it():
    assert length(CHAIN[:6], buildings=[(7, 0)]) == 6


def test_opponent_at_the_end_still_counts_up_to_it():
    assert length(CHAIN[:5], buildings=[(0, 1)]) == 5


# three separate stretches of coast, one per player, far apart
STRETCH = {0: COASTAL_EDGES[0:8], 1: COASTAL_EDGES[10:18], 2: COASTAL_EDGES[20:28]}


def game_with_roads(lengths, holder=-1):
    state = new_game(seed=42)
    for player, n in enumerate(lengths):
        for e in STRETCH[player][:n]:
            state.edge_owner[e] = player
    state.longest_road_holder = holder
    update_longest_road(state)
    return state


def test_nobody_holds_it_below_5():
    assert game_with_roads([4, 3, 0]).longest_road_holder == -1


def test_first_to_5_takes_it():
    state = game_with_roads([5, 3, 0])
    assert state.longest_road_holder == 0
    assert state.longest_road_len == [5, 3, 0]


def test_tying_the_holder_is_not_enough():
    assert game_with_roads([5, 5, 0], holder=0).longest_road_holder == 0


def test_strictly_longer_takes_it():
    assert game_with_roads([5, 6, 0], holder=0).longest_road_holder == 1


def test_no_holder_and_a_tie_means_nobody():
    assert game_with_roads([6, 6, 0]).longest_road_holder == -1


def test_holder_cut_below_5_loses_it():
    assert game_with_roads([4, 3, 0], holder=0).longest_road_holder == -1


def test_holder_cut_and_a_tie_among_others_means_nobody():
    assert game_with_roads([4, 6, 6], holder=0).longest_road_holder == -1


def test_holder_cut_but_still_tied_for_longest_keeps_it():
    assert game_with_roads([6, 6, 0], holder=0).longest_road_holder == 0


def test_settlement_that_cuts_a_road_moves_the_bonus():
    # P1 holds with 7; P0 has 6. P0 builds on a corner in the middle of P1's road
    state = game_with_roads([6, 7, 0], holder=1)
    middle = EDGE_VERTICES[STRETCH[1][3]][0]
    state.phase = Phase.MAIN
    state.current_player = 0
    state.hands[0] = [1, 1, 1, 1, 0]
    state.bank = [18, 18, 18, 18, 19]
    state.edge_owner[next(e for e in VERTEX_EDGES[middle] if state.edge_owner[e] == -1)] = 0
    after = apply(state, BuildSettlement(middle), random.Random(0))
    assert max(after.longest_road_len[1:]) < 6
    assert after.longest_road_holder == 0
    assert victory_points(after, 0) == 1 + 2
