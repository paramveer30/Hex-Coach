import time

from hexcoach.bots.random_bot import RandomBot
from hexcoach.sim.runner import play_game


def random_bots():
    return [RandomBot(), RandomBot(), RandomBot()]


def test_same_seed_plays_the_same_game():
    assert play_game(random_bots(), seed=7) == play_game(random_bots(), seed=7)


def test_random_games_finish_with_a_10_point_winner():
    for seed in range(50):
        result = play_game(random_bots(), seed)
        assert result.winner is not None
        assert result.vp[result.winner] >= 10
        assert all(vp < 10 for p, vp in enumerate(result.vp) if p != result.winner)


def test_at_least_20_random_games_per_second():
    start = time.perf_counter()
    for seed in range(40):
        play_game(random_bots(), seed)
    games_per_second = 40 / (time.perf_counter() - start)
    assert games_per_second >= 20
