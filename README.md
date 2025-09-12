# Disk Catalogue

Version: 0.1.1


Early-stage toolkit for scanning mounted volumes and exploring metadata (paths, sizes) via DuckDB.

## Quick Start (Dev Container)

1. Open repository in VS Code.
2. Reopen in container when prompted.
3. (Optional) Install dependencies editable: `uv pip install -e .[dev]` or `pip install -e .[dev]`.
4. Run tests: `pytest`.
5. Format & lint: `ruff check . && ruff format .` (or `black .`).

## Features (initial)

- Recursive file scanning
- Returns structured `FileRecord` objects
- TDD scaffold (pytest, coverage, mypy, ruff, black)

## Roadmap

See `CHANGELOG.md` and `COPILOT_INSTRUCTIONS.md` for future ideas.

## License

MIT
