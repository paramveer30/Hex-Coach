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
