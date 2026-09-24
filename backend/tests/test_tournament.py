from collections import Counter

import pytest

from hexcoach.sim.tournament import run_tournament, seat_schedule, to_markdown


def test_rotation_puts_every_bot_in_every_seat_equally():
    schedule = seat_schedule(num_bots=3, games=30, seed=42, rotate=True)
    seats = Counter((order[seat], seat) for _, order in schedule for seat in range(3))
    assert set(seats.values()) == {10}
    assert len(seats) == 9


def test_rotation_plays_each_board_once_per_seating():
    schedule = seat_schedule(num_bots=3, games=6, seed=42, rotate=True)
    assert [s for s, _ in schedule] == [42, 42, 42, 43, 43, 43]
    assert [o for _, o in schedule[:3]] == [[0, 1, 2], [1, 2, 0], [2, 0, 1]]


def test_rotation_needs_a_multiple_of_the_bot_count():
    with pytest.raises(ValueError):
        seat_schedule(num_bots=3, games=10, seed=0, rotate=True)


def test_without_rotation_every_game_gets_a_new_board():
    schedule = seat_schedule(num_bots=3, games=4, seed=7, rotate=False)
    assert [s for s, _ in schedule] == [7, 8, 9, 10]
    assert all(order == [0, 1, 2] for _, order in schedule)


def test_wins_and_draws_add_up_to_games():
    summary = run_tournament(["heuristic", "random", "random"], games=12, seed=1)
    assert sum(b["wins"] for b in summary["bots"]) + summary["draws"] == 12
    for b in summary["bots"]:
        assert b["ci_low"] <= b["win_rate"] <= b["ci_high"]


def test_same_seed_same_tournament():
    a = run_tournament(["heuristic", "random", "random"], games=6, seed=5)
    b = run_tournament(["heuristic", "random", "random"], games=6, seed=5)
    a.pop("runtime_s")
    b.pop("runtime_s")
    assert a == b


def test_markdown_names_every_bot_and_the_baseline():
    table = to_markdown(run_tournament(["heuristic", "random", "random"], games=3, seed=2))
    assert "0: heuristic" in table and "2: random" in table
    assert "33.3%" in table
