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

## 2026-09-24: assert_invariants lives in the engine but runs only in tests
Context: Spec 6.5 lists invariants to check: cards conserved, no negatives, piece limits, distance rule, roads connected, VP consistent, robber on the board.
Decision: `engine/invariants.py` has one check per invariant plus `assert_invariants`. Tests call it after every move; the game loop does not. Measured: 100 random games, 89,628 moves, all checked in 9.9s. The roads check lets road groups join through any corner, since an opponent can legally build in the middle of your road later.
Tradeoff: About 10x slower with checks on, so they stay out of normal play and benchmarks.

## 2026-09-24: Longest Road recomputed after setup roads too
Context: The first invariant run failed: after a setup road, the stored road length was 0 but the real length was 1, because PlaceSetupRoad never called update_longest_road.
Decision: PlaceSetupRoad now calls update_longest_road.
Tradeoff: None; setup roads can't reach 5, but bots and the coach will read these lengths.

## 2026-09-24: Property tests use 40/20/20 examples per run
Context: Each hypothesis example plays a full game (up to ~450 ms with invariants on). The suite should stay fast.
Decision: `tests/test_properties.py` runs 40 seeds for invariants, 20 for apply-never-mutates, 20 for same-seed-same-game, with `deadline=None`. Each run draws new seeds, so coverage grows over time. The full 1,000-game check runs by hand: 1,000 games, 905,493 moves, 0 crashes, 0 invariant failures, 218 s.
Tradeoff: A single test run covers only 80 games; rare bugs may take several runs to surface.

## 2026-09-24: Frontend dependencies: Next.js 16, React 19, TypeScript, Tailwind 4, zustand
Context: The UI was built ahead of Phase 3 at Param's request. The spec picks Next.js (App Router), TypeScript, Tailwind, and zustand.
Decision: Scaffolded with create-next-app (Next.js 16.3.6, React 19.2.8, Tailwind 4, ESLint 9) and added zustand 5. No other runtime dependencies. The scaffold's AGENTS.md is excluded via .git/info/exclude.
Tradeoff: Next.js 16 changes some conventions from older versions (for example `params` is a Promise); we follow its bundled docs.

## 2026-09-24: UI runs on exported fixtures until the API exists
Context: The FastAPI server is Phase 3 work to build together; the UI needed real board data now.
Decision: A one-off script exported `frontend/lib/fixtures/geometry.json` (engine geometry tables) and `sample-game.json` (a heuristic-bot game, seed 7, stopped at turn 38 mid main phase). The UI reads those; buttons show costs and disabled reasons but don't send moves. A banner says it's a preview.
Tradeoff: The fixture can drift from the engine if geometry or state fields change; it gets replaced by `/api/geometry` and `/api/games/{id}` in Phase 3.

## 2026-09-24: Board art is hand-drawn inline SVG
Context: The board is the product's one memorable thing (spec 11.4).
Decision: Every tile, piece, port, and the robber is inline SVG built from the engine's pixel coordinates. The coastline is the union of oversized hexes behind the tiles. Player colors come from the Okabe-Ito color-blind-safe palette (ivory, sky, rose). Transforms are rounded to 2 decimals because the server and browser computed `atan2` differently in the last digit and caused a hydration mismatch.
Tradeoff: About 1,480 SVG nodes and 56 drop-shadow filters on the game page; measured one frame at about 20 ms. Revisit if animation later makes it janky.

## 2026-09-24: Heuristic bot interpretations of spec 7.2
Context: Spec 7.2 gives the scoring formula and priorities but leaves a few details open.
Decision: A 2:1 port counts if the player produces that resource now or would from this spot. "Within 2 edges" means an open settlement spot at either end of the new road or one step past it. A bank trade is made whenever it makes a city, settlement, or road affordable right away (checked in that priority order). Discards pick among the 5 engine candidates the one that keeps the most toward the current goal (city, else settlement, else road), so the bot only ever returns legal actions. Ties go to the first option in legal_actions order, so the bot is deterministic.
Tradeoff: No lookahead and no longest-road planning. Weights stay at the spec's starting values (1.5, 1, 2) until a tournament exists to tune them.

## 2026-09-24: Phase 2 benchmark results (heuristic bot, speed, cap rate)
Context: Phase 2 done checks and the open question about the turn cap rate.
Decision: Recorded, fixed seeds 0..199 or 0..299. Heuristic vs 2 random: 197/200 wins, 98.5% +/- 1.7% (95% CI), 1 draw, 4 capped. Heuristic x3: median 86 turns, 0 of 300 capped, 0 draws, wins by seat 109/106/85. Random x3: median 336 turns, 103 of 300 capped. Speed, random x3: 41 games/s tonight versus 84 earlier; the code at commit 092f563 measured 42 games/s back to back with the current code (identical 95,756 total turns), so the drop is the machine throttling while locked, not the engine.
Tradeoff: The turn cap is rare with sensible bots, so no rule change. Re-measure speed on a plugged-in, awake machine before quoting it in the README.

## 2026-09-24: UI redesign: dark table theme, less text, teaching highlights
Context: Param found the first UI crowded, text-heavy, and dull.
Decision: A dark "game table" theme (tokens in `frontend/app/globals.css`: table #0C171D, surface #132730, gold accent #F0C05A; tile and piece colors unchanged), a compact sidebar, the player's hand as cards in the bottom dock, and board highlights. The sample fixture now includes the engine's real legal build spots, so choosing a build pulses exactly those spots and tapping one shows a ghost piece. The opening trainer shows the spec 7.2 quick score as a heatmap on a fresh board (seed 11). The palette change is pending approval as a spec 11.4 change.
Tradeoff: The fixture must be re-exported when state fields change; replaced by the API in Phase 3.

## 2026-09-24: Coach nudges in the UI are rules-level only
Context: Four coach modes (off, ask, nudge, always) were requested; real move advice needs the search bot (Phase 4) and the coach (Phase 6).
Decision: For now, Nudge and Always only say what the rules allow ("you can afford a settlement, and 1 spot is open"), computed from the engine's legal spots. The Hint button stays disabled until search exists. The modes are pending approval as a Phase 6 spec change.
Tradeoff: No strategic advice yet; the UI plumbing (modes, banner, highlights) is ready for it.

## 2026-09-24: CI on GitHub Actions
Context: Spec 12 asks for ruff, pytest, a 200-game smoke test, and frontend type check and lint on every push.
Decision: `.github/workflows/ci.yml` with two jobs. Backend: `uv sync --locked`, ruff check and format, pytest, 200 random games. Frontend: `npm ci`, `next typegen` (Next 16 generates the route types `layout.tsx` uses), `tsc --noEmit`, lint.
Tradeoff: `test_at_least_20_random_games_per_second` depends on machine speed and may be flaky on shared CI runners (audit M4).

## 2026-09-24: Tournament uses a paired, rotated seating schedule
Context: Identical heuristic bots won 109 / 106 / 85 games by seat (300 games), and boards vary in how much they favor each seat. Spec 9.1 asks for --rotate-seats.
Decision: With rotation, each board seed is played once per seating (3 games for 3 bots), each bot moving one seat along: A B C, B C A, C A B. Games must be a multiple of the bot count. `play_game` gained `shuffle_seats=False` so the tournament controls seating. Win rates are reported with a 95% normal-approximation interval, clipped to [0, 1].
Tradeoff: Games come in multiples of 3; the normal approximation is loose near 0% and 100% (a Wilson interval would be tighter there), fine for the rates we report.

## 2026-09-24: Speed is benchmarked, not unit-tested
Context: `test_at_least_20_random_games_per_second` measured 84, 41, and 13.6 games/s on the same code depending on whether the laptop was throttling, so it failed with no code change (audit M4).
Decision: Removed it from the test suite. `uv run python -m hexcoach.sim.bench` reports random games per second against the target of 20. Measured today: 85 games/s.
Tradeoff: A speed regression no longer fails CI; it shows up when we run the benchmark and log the number here.

## 2026-09-24: Phase 2 benchmark: heuristic vs 2 random, rotated
Context: Phase 2 done check (more than 90% against random bots), now with seat rotation and confidence intervals.
Decision: `python -m hexcoach.sim.tournament --bots heuristic,random,random --games 300 --rotate-seats --seed 42` gave 297 wins, 99.0% (95% CI 97.9% to 100.0%), 1 draw, 2 turn-cap hits, 86 turns on average, 1.66 s. Results saved to `backend/results/heuristic_vs_random.json`.
Tradeoff: None; this is the baseline the MCTS bot must beat in Phase 4.
