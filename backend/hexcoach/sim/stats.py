"""Statistics for benchmark results."""

import math

Z_95 = 1.96


def win_rate_ci(wins: int, games: int) -> tuple[float, float, float]:
    """Return (win_rate, low, high): the rate and its 95% interval, clipped to [0, 1]."""
    if games == 0:
        raise ValueError("need at least one game to estimate a win rate")
    rate = wins / games
    margin = Z_95 * math.sqrt(rate * (1 - rate) / games)
    return rate, max(0.0, rate - margin), min(1.0, rate + margin)
