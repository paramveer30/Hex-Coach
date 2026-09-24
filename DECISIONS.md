# Decisions

A log of every rule simplification, threshold, tuning value, tradeoff, and added dependency.

## 2026-09-22: Python 3.12 pinned, uv for packaging
Context: The machine has both 3.12 and 3.14 installed, and the spec calls for 3.12.
Decision: `backend/.python-version` pins 3.12 and `requires-python` is `>=3.12,<3.13`. uv manages the virtualenv and `uv.lock` pins exact versions.
Tradeoff: We don't get 3.14 speedups, but every machine and the Docker image run the same interpreter.

## 2026-09-22: Dev dependencies: pytest, hypothesis, ruff
Context: Phase 1 needs unit tests, property-based tests (used from Phase 2), and one lint/format tool.
Decision: Added all three as dev dependencies only, so they never ship in the server image.
Tradeoff: None meaningful; these are the spec's chosen tools.

## 2026-09-22: Backend package not installed, imported via pytest pythonpath
Context: `hexcoach` lives at `backend/hexcoach/` with no build backend.
Decision: pytest's `pythonpath = ["."]` makes it importable in tests; CLIs run as `uv run python -m hexcoach...` from `backend/`.
Tradeoff: Can't `import hexcoach` from outside `backend/`. Revisit if the Rust build in Phase 12 needs a real build backend.

## 2026-09-22: Pointy-top hexes, HEX_SIZE 60, corners rounded to 3 decimals
Context: Vertices are found by computing every hex corner and deduplicating, which needs float noise removed.
Decision: Pointy-top orientation (rows of 3-4-5-4-3), 60 px center-to-corner, positions rounded to 3 decimals. Ids are assigned in reading order (top to bottom, left to right).
Tradeoff: 3 decimals is far coarser than float error and far finer than the 60 px spacing, so it can't merge distinct corners or split one. The frontend scales with an SVG viewBox rather than asking for another size.

## 2026-09-22: Port positions use a 3-3-4 gap pattern around the coast
Context: The spec fixes port positions but doesn't say which of the 30 coastal edges they're on.
Decision: Walk the coastal edges clockwise from just above the left point and place a port every 3, 3, 4, 3, 3, 4, 3, 3, 4 edges (`PORT_GAPS` in `geometry.py`).
Tradeoff: Close to the classic board's even spread but not an exact copy of any printed layout. Gaps of 3+ guarantee no vertex touches two ports.

## 2026-09-22: Resources and ports stored as small ints
Context: State must be compact and fast to copy for search.
Decision: Resources are ints 0-4 (wood, brick, sheep, wheat, ore). The desert is -1 and a generic 3:1 port is -1. `Board` is a frozen dataclass of tuples.
Tradeoff: Less readable than enums when printed, but cheap to compare, hash, and index into hands.

## 2026-09-22: No adjacent 6/8 enforced by reshuffling all tokens
Context: The spec says resample until no two red numbers touch.
Decision: Reshuffle the whole token list until valid. Measured: 14.1% of shuffles are valid, so about 7 shuffles per board, 16 us per board.
Tradeoff: Unbounded loop in theory, but it's fast and every valid layout stays equally likely. Swapping only the offending tokens would be faster but biases the distribution.

## 2026-09-22: GameState adds setup_vertex; clone copies lists by hand
Context: In setup, the road must touch the settlement just placed, and the spec's state has no field for it. MCTS will clone state thousands of times per move.
Decision: Added `setup_vertex` (-1 when unused). `clone()` builds a new GameState with sliced lists and a per-player copy of `hands`, sharing the frozen `Board`. Measured 0.98 us per clone.
Tradeoff: A new field must also be added to `clone()` by hand; `test_clone_covers_every_field` catches a miss. `copy.deepcopy` would be automatic but far slower and would copy the board too.

## 2026-09-23: apply() trusts that the action is legal
Context: Bots only pick from legal_actions, and re-checking legality inside apply would slow every simulated move.
Decision: apply() does not re-validate moves. The API layer (Phase 3) checks human moves against legal_actions before calling apply.
Tradeoff: Calling apply with an illegal action directly can produce a broken state. Phase 2's invariant checks and property tests will catch that in testing.

## 2026-09-23: Seat order randomized by the runner, not the engine
Context: The spec randomizes seat order at game start. Inside the engine, players are just 0, 1, 2.
Decision: The engine always starts setup with player 0. The game runner shuffles which bot or human sits in which seat, using the game's seed.
Tradeoff: None for the rules; it keeps new_game simple and the seat mapping visible to the caller.

## 2026-09-23: Temporary: a 7 does nothing in Phase 1
Context: Discards, the robber, and stealing are Phase 2 work.
Decision: Rolling a 7 skips production and goes straight to the main phase. Replaced in Phase 2.
Tradeoff: Phase 1 games are slightly richer than real ones (no discards, no robber blocking).

## 2026-09-23: Temporary: bank shortage pays nobody
Context: The full shortage rule (a single owed player gets whatever is left) is Phase 2 work.
Decision: If the bank can't cover everyone owed a resource on a roll, nobody gets that resource. Replaced in Phase 2.
Tradeoff: Rare in practice this early; the one-player case is slightly wrong until then.

## 2026-09-23: Phase 1 runner stops at 5000 turns as a safety net
Context: Measured over 200 random-vs-random games: 32 games/sec, median 272 turns, 32 games over 400 turns. One game (seed 85) can never end: all players have used their cities, can't place a settlement, and sit at 9/9/8 VP.
Decision: `sim/runner.py` stops at 5000 turns and reports no winner. This is not the game's turn cap.
Tradeoff: Rare no-winner results until Phase 2 adds Longest Road (+2 VP) and the 400-turn cap, which end these games by the rules.

## 2026-09-23: Full bank shortage rule and 400-turn cap (replaces two temporary entries)
Context: Phase 1 paid nobody when the bank was short and had no turn cap, only a 5000-turn runner safety net.
Decision: If the bank can't cover everyone owed a resource, a single owed player gets whatever is left; two or more get nothing. At 400 turns the game ends and the VP leader wins; a tie is a draw (winner None). The runner's safety net is removed.
Tradeoff: Measured over 200 random-vs-random games: 136 games/sec, 31 ended by the cap (15.5%), 8 draws. That's not "rare" yet, but random bots waste turns trading. Re-check the cap rate with heuristic bots.

## 2026-09-23: Discard candidates capped at 5 in legal_actions
Context: Discarding half of a large hand has dozens of combinations, which explodes search branching.
Decision: `discard_candidates` builds one discard per resource to protect: remove cards from the largest piles first, touching the protected resource last. Duplicates dropped, at most 5. `apply` still accepts any valid discard, so humans can pick anything.
Tradeoff: Bots can't find unusual discards. Tests check every hand of 0-3 of each resource gives valid, distinct candidates.

## 2026-09-23: player_to_move() separates "whose turn" from "who acts now"
Context: During DISCARD, players other than the roller must act.
Decision: `player_to_move(state)` returns the first pending discarder in DISCARD, otherwise `current_player`. The runner asks that player for a move.
Tradeoff: Every caller that asks a bot for a move must use `player_to_move`, not `current_player`.

## 2026-09-23: Sevens make random-vs-random games hit the turn cap more
Context: Measured over 300 random-vs-random games with the full 7 rules: 104 games/sec, 154 ended by the 400-turn cap (51%), 30 draws. Card conservation checked after every move in 200 games: zero violations.
Decision: No rule change. Random bots rarely build, hold big hands, and lose half on 7s, so they stall.
Tradeoff: Random-vs-random cap rate is not a meaningful health metric. Re-check the cap rate with heuristic bots.

## 2026-09-23: Longest Road holder rules, including a cut below 5
Context: Spec 5.8 covers ties and breaks but not a holder cut below 5 while nobody else has 5+.
Decision: The holder loses it in that case (standard printed rules), so "you need 5+ to hold it" is always true. Full order in `update_longest_road`: nobody at 5+ means no holder; the holder keeps it while tied for best; a unique best player takes it; otherwise nobody holds it.
Tradeoff: None beyond matching the printed rules.

## 2026-09-23: Longest Road recomputed for all players after each road or settlement
Context: The spec suggests recomputing only affected players.
Decision: Recompute every player's length with a DFS (`engine/longest_road.py`) after each BuildRoad and BuildSettlement. Measured over 300 random games: 104 -> 84 games/sec. Capped games dropped from 154 to 103 because the +2 VP ends more games.
Tradeoff: About 19% slower, still over 4x the 20 games/sec target. Recompute only affected players if profiling later shows it matters.

## 2026-09-23: Win checked when a player's turn begins
Context: Cutting the holder's road can give Longest Road to a third player during someone else's turn. The spec says a player wins during their own turn.
Decision: EndTurn runs check_win for the incoming player before the turn cap check.
Tradeoff: That player wins at the start of their turn rather than instantly.
