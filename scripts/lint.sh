#!/usr/bin/env bash
set -euo pipefail

if [ -d .venv ]; then
  source .venv/bin/activate
fi

ruff check .
ruff format --check . || true
black --check . || true
mypy .
