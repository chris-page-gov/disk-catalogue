# Repository Guidelines

## Project Structure & Module Organization
- `src/disk_catalogue/`: Python package (scanner and public API).
- `tests/`: Pytest suite (`test_*.py`).
- `scripts/`: Dev and data tooling (lint, tests, CSV/DuckDB helpers).
- `output/`: Generated CSVs from drive scans (gitignored).
- Root SQL/CSV docs: `duckdb_schema.sql`, `sample_queries.sql`, `drive_manifest.csv`.

## Build, Test, and Development Commands
- Install (editable, with dev tools): `pip install -e .[dev]` (or `uv pip install -e .[dev]`).
- Run tests (with coverage via pyproject): `pytest` or `scripts/run_tests.sh`.
- Lint/format/type-check: `scripts/lint.sh` (runs ruff, black --check, mypy).
- Format code: `ruff format .` (or `black .`).

## Coding Style & Naming Conventions
- Python 3.11, 4‑space indent, LF endings; max line length 100.
- Use `ruff` (rules: E,F,W,I,B,C4,UP,RUF) and `black` for formatting.
- Types: `mypy --strict` is enabled; add/maintain type hints.
- Naming: modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Package import path is `disk_catalogue` (ensure code lives under `src/`).

## Testing Guidelines
- Framework: `pytest` with `pytest-cov` (configured in `pyproject.toml`).
- Name tests `test_*.py`; prefer small, deterministic unit tests.
- Keep/raise coverage when changing behavior; add tests for regressions.
- Use `tmp_path` and fixtures for filesystem interactions.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (see `commit-template.txt`): `type(scope): subject`.
  Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci.
- PRs: include clear description, linked issues, and before/after notes. For data/CLI changes, show example command/output.
- Run `scripts/lint.sh` and `pytest` locally before opening a PR.

## Security & Configuration Tips
- Do not commit secrets or local paths; `.env*`, output CSVs, and DuckDB files are gitignored.
- When scanning drives, prefer the dev container and read‑only mounts (see `build.md`).
- Large data belongs in `output/` and stays out of version control.

## Agent-Specific Notes
- Make minimal, focused changes; do not rename files or APIs without discussion.
- Obey these guidelines for any files you touch and update docs/tests alongside code changes.
