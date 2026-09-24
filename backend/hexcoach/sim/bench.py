"""Engine speed in random games per second. Reported, not asserted: it depends on the machine."""

import argparse
import time

from hexcoach.bots.random_bot import RandomBot
from hexcoach.sim.runner import play_game

TARGET = 20


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure random-vs-random games per second.")
    parser.add_argument("--games", type=int, default=200)
    args = parser.parse_args()

    bots = [RandomBot(), RandomBot(), RandomBot()]
    start = time.perf_counter()
    for seed in range(args.games):
        play_game(bots, seed)
    rate = args.games / (time.perf_counter() - start)
    print(f"{args.games} random games: {rate:.0f} games/s (target {TARGET})")


if __name__ == "__main__":
    main()
