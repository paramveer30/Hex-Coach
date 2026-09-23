"""Play one headless game between bots from a seed."""

import argparse
import random
from dataclasses import dataclass

from hexcoach.bots.base import Bot
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.rules import apply, is_terminal, new_game, victory_points, winner

# safety net only; the real 400-turn cap is a game rule added in Phase 2
MAX_TURNS = 5000


@dataclass
class GameResult:
    seed: int
    seats: list[str]  # bot name per player id
    winner: int | None
    turns: int
    moves: int
    vp: list[int]


def play_game(bots: list[Bot], seed: int) -> GameResult:
    rng = random.Random(seed)
    seats = list(bots)
    rng.shuffle(seats)

    state = new_game(seed, num_players=len(seats))
    moves = 0
    while not is_terminal(state) and state.turn_number < MAX_TURNS:
        action = seats[state.current_player].choose(state, rng)
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
    print(f"seed {result.seed}: player {result.winner} wins after {result.turns} turns")
    print(f"moves played: {result.moves}")
    for p, (name, vp) in enumerate(zip(result.seats, result.vp, strict=True)):
        print(f"  player {p} ({name}): {vp} VP")


if __name__ == "__main__":
    main()
