import pytest

from hexcoach.sim.stats import win_rate_ci


def test_our_heuristic_result():
    rate, low, high = win_rate_ci(197, 200)
    assert rate == pytest.approx(0.985)
    assert low == pytest.approx(0.985 - 0.01685, abs=1e-4)
    assert high == pytest.approx(1.0)


def test_half_of_300_games_is_about_plus_or_minus_5_7_points():
    rate, low, high = win_rate_ci(150, 300)
    assert rate == pytest.approx(0.5)
    assert high - rate == pytest.approx(0.0566, abs=1e-3)
    assert rate - low == pytest.approx(0.0566, abs=1e-3)


def test_interval_never_leaves_0_to_1():
    assert win_rate_ci(0, 10) == (0.0, 0.0, 0.0)
    assert win_rate_ci(10, 10) == (1.0, 1.0, 1.0)


def test_more_games_means_a_narrower_interval():
    _, lo_small, hi_small = win_rate_ci(60, 100)
    _, lo_big, hi_big = win_rate_ci(600, 1000)
    assert hi_big - lo_big < hi_small - lo_small


def test_zero_games_is_an_error():
    with pytest.raises(ValueError):
        win_rate_ci(0, 0)
