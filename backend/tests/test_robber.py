import random
from itertools import product

from hexcoach.engine.actions import Discard, MoveRobber, Steal
from hexcoach.engine.geometry import HEX_VERTICES
from hexcoach.engine.rules import (
    apply,
    discard_candidates,
    legal_actions,
    new_game,
    player_to_move,
)
from hexcoach.engine.state import Phase


def after_seven(hands):
    # force a 7 by trying rng seeds until one rolls it
    state = new_game(seed=42)
    state.phase = Phase.ROLL
    state.hands = [h[:] for h in hands]
    state.bank = [19 - sum(h[r] for h in hands) for r in range(5)]
    for seed in range(100):
        after = apply(state, legal_actions(state)[0], random.Random(seed))
        if after.last_roll == 7:
            return after
    raise AssertionError("no 7 in 100 seeds")


def test_only_players_over_7_cards_discard():
    state = after_seven([[2, 2, 2, 1, 0], [3, 3, 3, 0, 0], [7, 0, 0, 0, 0]])
    assert state.phase == Phase.DISCARD
    assert state.pending_discards == [1]
    assert player_to_move(state) == 1


def test_nobody_over_7_skips_straight_to_the_robber():
    state = after_seven([[1, 1, 1, 1, 1], [0] * 5, [7, 0, 0, 0, 0]])
    assert state.phase == Phase.MOVE_ROBBER


def test_discard_candidates_are_valid_distinct_and_at_most_5():
    for hand in product(range(4), repeat=5):
        hand = list(hand)
        if sum(hand) <= 7:
            continue
        candidates = discard_candidates(hand)
        assert 1 <= len(candidates) <= 5
        assert len(set(candidates)) == len(candidates)
        for d in candidates:
            assert sum(d.counts) == sum(hand) // 2
            assert all(0 <= n <= have for n, have in zip(d.counts, hand, strict=True))


def test_discards_happen_in_order_then_robber():
    state = after_seven([[5, 4, 0, 0, 0], [0, 0, 4, 4, 0], [0] * 5])
    assert state.pending_discards == [0, 1]
    state = apply(state, Discard((3, 1, 0, 0, 0)), random.Random(0))
    assert state.hands[0] == [2, 3, 0, 0, 0]
    assert player_to_move(state) == 1
    state = apply(state, Discard((0, 0, 2, 2, 0)), random.Random(0))
    assert state.phase == Phase.MOVE_ROBBER
    assert state.bank == [17, 16, 17, 17, 19]


def robber_phase_with_building(owner, owner_hand):
    state = new_game(seed=42)
    state.phase = Phase.MOVE_ROBBER
    state.current_player = 0
    v = HEX_VERTICES[5][0]
    state.vertex_owner[v] = owner
    state.vertex_level[v] = 1
    state.hands[owner] = owner_hand
    return state


def test_robber_must_move_to_a_different_hex():
    state = robber_phase_with_building(1, [1, 0, 0, 0, 0])
    moves = legal_actions(state)
    assert len(moves) == 18
    assert MoveRobber(state.robber_hex) not in moves


def test_moving_onto_an_opponent_with_cards_leads_to_steal():
    state = apply(robber_phase_with_building(1, [1, 0, 0, 0, 0]), MoveRobber(5), random.Random(0))
    assert state.phase == Phase.STEAL
    assert legal_actions(state) == [Steal(1)]


def test_no_steal_from_empty_hands_or_yourself():
    state = apply(robber_phase_with_building(1, [0] * 5), MoveRobber(5), random.Random(0))
    assert state.phase == Phase.MAIN
    state = apply(robber_phase_with_building(0, [3, 0, 0, 0, 0]), MoveRobber(5), random.Random(0))
    assert state.phase == Phase.MAIN


def test_steal_moves_exactly_one_card():
    state = apply(robber_phase_with_building(1, [0, 0, 0, 3, 1]), MoveRobber(5), random.Random(0))
    after = apply(state, Steal(1), random.Random(0))
    assert sum(after.hands[1]) == 3
    assert sum(after.hands[0]) == sum(state.hands[0]) + 1
    assert after.phase == Phase.MAIN


def test_robber_blocks_the_hex_it_moves_to():
    state = apply(robber_phase_with_building(1, [0] * 5), MoveRobber(5), random.Random(0))
    assert state.robber_hex == 5
