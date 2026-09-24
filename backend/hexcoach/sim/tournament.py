"""Many games between bots, with seat rotation, reported as win rates with confidence intervals."""

import argparse
import json
import time
from pathlib import Path

from hexcoach.bots.heuristic import HeuristicBot
from hexcoach.bots.random_bot import RandomBot
from hexcoach.engine.rules import TURN_CAP
from hexcoach.sim.runner import play_game
from hexcoach.sim.stats import win_rate_ci

BOTS = {"random": RandomBot, "heuristic": HeuristicBot}


def seat_schedule(
    num_bots: int, games: int, seed: int, rotate: bool
) -> list[tuple[int, list[int]]]:
    # each entry is (board seed, order): order[seat] is the index of the bot sitting there.
    # with rotation, every board is played num_bots times, each bot moving one seat along
    if rotate and games % num_bots:
        raise ValueError(f"with --rotate-seats, games must be a multiple of {num_bots}")
    schedule = []
    for g in range(games):
        if rotate:
            shift = g % num_bots
            order = [(seat + shift) % num_bots for seat in range(num_bots)]
            schedule.append((seed + g // num_bots, order))
        else:
            schedule.append((seed + g, list(range(num_bots))))
    return schedule


def run_tournament(bot_names: list[str], games: int, seed: int, rotate: bool = True) -> dict:
    bots = [BOTS[name]() for name in bot_names]
    wins = [0] * len(bots)
    draws = turns = cap_hits = 0
    start = time.perf_counter()

    for board_seed, order in seat_schedule(len(bots), games, seed, rotate):
        result = play_game([bots[i] for i in order], board_seed, shuffle_seats=False)
        turns += result.turns
        cap_hits += result.turns >= TURN_CAP
        if result.winner is None:
            draws += 1
        else:
            wins[order[result.winner]] += 1

    report = []
    for i, name in enumerate(bot_names):
        rate, low, high = win_rate_ci(wins[i], games)
        report.append(
            {
                "bot": i,
                "name": name,
                "wins": wins[i],
                "win_rate": rate,
                "ci_low": low,
                "ci_high": high,
            }
        )
    return {
        "bots": report,
        "games": games,
        "seed": seed,
        "rotate_seats": rotate,
        "draws": draws,
        "avg_turns": turns / games,
        "turn_cap_hits": cap_hits,
        "runtime_s": round(time.perf_counter() - start, 2),
    }


def to_markdown(summary: dict) -> str:
    baseline = 1 / len(summary["bots"])
    lines = [
        "| Bot | Wins | Win rate | 95% CI |",
        "| --- | --- | --- | --- |",
    ]
    for b in summary["bots"]:
        lines.append(
            f"| {b['bot']}: {b['name']} | {b['wins']} | {b['win_rate']:.1%} "
            f"| {b['ci_low']:.1%} to {b['ci_high']:.1%} |"
        )
    lines.append("")
    lines.append(
        f"{summary['games']} games, {summary['draws']} draws, "
        f"{summary['avg_turns']:.0f} turns on average, "
        f"{summary['turn_cap_hits']} hit the turn cap, "
        f"{summary['runtime_s']} s. Baseline for an equal bot: {baseline:.1%}."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bot tournament.")
    parser.add_argument(
        "--bots", default="heuristic,random,random", help="comma-separated: " + ", ".join(BOTS)
    )
    parser.add_argument("--games", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rotate-seats", action="store_true")
    parser.add_argument("--out", type=Path, help="write the full results as JSON here")
    args = parser.parse_args()

    summary = run_tournament(args.bots.split(","), args.games, args.seed, args.rotate_seats)
    print(to_markdown(summary))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
