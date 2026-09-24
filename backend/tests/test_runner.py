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


class Ann(RandomBot):
    pass


class Bea(RandomBot):
    pass


class Cal(RandomBot):
    pass


def test_fixed_seats_keep_the_given_order():
    bots = [Ann(), Bea(), Cal()]
    assert play_game(bots, seed=3, shuffle_seats=False).seats == ["Ann", "Bea", "Cal"]
    rotated = bots[1:] + bots[:1]
    assert play_game(rotated, seed=3, shuffle_seats=False).seats == ["Bea", "Cal", "Ann"]
