"""Play one headless game between bots from a seed."""

import argparse
import random
from dataclasses import dataclass

from hexcoach.bots.base import Bot
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.rules import (
    apply,
    is_terminal,
    new_game,
    player_to_move,
    victory_points,
    winner,
)


@dataclass
class GameResult:
    seed: int
    seats: list[str]  # bot name per player id
    winner: int | None
    turns: int
    moves: int
    vp: list[int]


def play_game(bots: list[Bot], seed: int, shuffle_seats: bool = True) -> GameResult:
    rng = random.Random(seed)
    seats = list(bots)
    # tournaments pass shuffle_seats=False and rotate seats themselves, so every bot
    # sits in every seat equally often
    if shuffle_seats:
        rng.shuffle(seats)

    state = new_game(seed, num_players=len(seats))
    moves = 0
    while not is_terminal(state):
        action = seats[player_to_move(state)].choose(state, rng)
        state = apply(state, action, rng)
        moves += 1

    return GameResult(
        seed=seed,
        seats=[type(bot).__name__ for bot in seats],
        winner=winner(state),
        turns=state.turn_number,
        moves=moves,
        vp=[victory_points(state, p) for p in range(len(seats))],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Play one random-vs-random game.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = play_game([RandomBot(), RandomBot(), RandomBot()], args.seed)
    if result.winner is None:
        print(f"seed {result.seed}: draw after {result.turns} turns")
    else:
        print(f"seed {result.seed}: player {result.winner} wins after {result.turns} turns")
    print(f"moves played: {result.moves}")
    for p, (name, vp) in enumerate(zip(result.seats, result.vp, strict=True)):
        print(f"  player {p} ({name}): {vp} VP")


if __name__ == "__main__":
    main()
