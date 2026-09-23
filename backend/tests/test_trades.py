import random

from hexcoach.engine.actions import BankTrade
from hexcoach.engine.board import GENERIC_PORT, ORE, SHEEP, WHEAT
from hexcoach.engine.geometry import PORT_VERTICES
from hexcoach.engine.rules import apply, legal_actions, new_game, trade_rate
from hexcoach.engine.state import Phase


def trades(state):
    return [a for a in legal_actions(state) if isinstance(a, BankTrade)]


def main_phase(hand):
    state = new_game(seed=42)
    state.phase = Phase.MAIN
    state.hands[0] = hand
    state.bank = [19 - n for n in hand]
    return state


def own_port(state, kind):
    port = state.board.port_type.index(kind)
    state.vertex_owner[PORT_VERTICES[port][0]] = 0
    state.vertex_level[PORT_VERTICES[port][0]] = 1


def test_default_rate_is_4():
    assert trade_rate(main_phase([0] * 5), 0, WHEAT) == 4
    assert trades(main_phase([0, 0, 3, 0, 0])) == []
    assert len(trades(main_phase([0, 0, 4, 0, 0]))) == 4


def test_generic_port_gives_3_for_any_resource():
    state = main_phase([0, 0, 3, 0, 0])
    own_port(state, GENERIC_PORT)
    assert all(trade_rate(state, 0, r) == 3 for r in range(5))
    assert BankTrade(SHEEP, ORE) in trades(state)


def test_specific_port_gives_2_for_that_resource_only():
    state = main_phase([0, 0, 0, 2, 2])
    own_port(state, WHEAT)
    assert trade_rate(state, 0, WHEAT) == 2
    assert trade_rate(state, 0, ORE) == 4
    assert BankTrade(WHEAT, ORE) in trades(state)
    assert not any(t.give == ORE for t in trades(state))


def test_cannot_ask_for_a_resource_the_bank_is_out_of():
    state = main_phase([0, 0, 4, 0, 0])
    state.bank[ORE] = 0
    assert BankTrade(SHEEP, ORE) not in trades(state)


def test_trade_moves_cards_both_ways():
    state = main_phase([0, 0, 4, 0, 0])
    after = apply(state, BankTrade(SHEEP, ORE), random.Random(0))
    assert after.hands[0] == [0, 0, 0, 0, 1]
    for r in range(5):
        assert after.bank[r] + after.hands[0][r] == 19
