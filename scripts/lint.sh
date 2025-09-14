#!/usr/bin/env bash
# Lint, format, and type-check the project.
#
# Usage:
#   scripts/lint.sh            # check mode (ruff, ruff format --check, black --check, mypy)
#   scripts/lint.sh --fix      # auto-fix (ruff --fix, ruff format, black) then mypy

set -euo pipefail

if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

MODE=${1:-check}

if [ "$MODE" = "--fix" ] || [ "$MODE" = "fix" ]; then
  echo "[lint] Auto-fix mode: ruff --fix, ruff format, black"
  ruff check --fix .
  ruff format .
  black .
else
  ruff check .
  ruff format --check . || true
  black --check . || true
fi

mypy .
