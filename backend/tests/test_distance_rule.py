from hexcoach.engine.geometry import NUM_VERTICES, VERTEX_NEIGHBORS
from hexcoach.engine.rules import settlement_spot_ok

EMPTY = -1


def board_with(*owned):
    vertex_owner = [EMPTY] * NUM_VERTICES
    for vertex, player in owned:
        vertex_owner[vertex] = player
    return vertex_owner


def test_every_spot_is_ok_on_an_empty_board():
    empty = board_with()
    assert all(settlement_spot_ok(empty, v) for v in range(NUM_VERTICES))


def test_spot_that_is_already_taken_is_not_ok():
    assert not settlement_spot_ok(board_with((22, 0)), 22)


def test_spot_next_to_any_building_is_not_ok():
    for neighbor in (16, 17, 28):
        assert not settlement_spot_ok(board_with((neighbor, 1)), 22)


def test_rule_applies_to_your_own_buildings_too():
    assert not settlement_spot_ok(board_with((16, 0)), 22)


def test_spot_two_steps_away_is_ok():
    assert settlement_spot_ok(board_with((11, 2), (33, 1)), 22)


def test_coastal_spot_with_only_two_neighbors():
    assert VERTEX_NEIGHBORS[0] == (3, 4)
    assert settlement_spot_ok(board_with(), 0)
    assert not settlement_spot_ok(board_with((4, 2)), 0)
