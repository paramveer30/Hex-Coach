import time

from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.rules import TURN_CAP
from hexcoach.sim.runner import play_game


def random_bots():
    return [RandomBot(), RandomBot(), RandomBot()]


def test_same_seed_plays_the_same_game():
    assert play_game(random_bots(), seed=7) == play_game(random_bots(), seed=7)


def test_random_games_end_by_10_points_or_the_turn_cap():
    for seed in range(100):
        result = play_game(random_bots(), seed)
        assert result.turns <= TURN_CAP
        if result.turns < TURN_CAP:
            assert result.vp[result.winner] >= 10
        elif result.winner is not None:
            assert result.vp[result.winner] == max(result.vp)


def test_at_least_20_random_games_per_second():
    start = time.perf_counter()
    for seed in range(40):
        play_game(random_bots(), seed)
    games_per_second = 40 / (time.perf_counter() - start)
    assert games_per_second >= 20
