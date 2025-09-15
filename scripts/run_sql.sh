#!/usr/bin/env bash
set -euo pipefail

# Run DuckDB SQL inside the Dev Container when available, otherwise on host.
#
# Usage examples:
#   scripts/run_sql.sh catalogue.duckdb          # Interactive shell
#   scripts/run_sql.sh catalogue.duckdb -c 'SELECT 1;'
#   scripts/run_sql.sh :memory: -c 'SELECT 42;'
#
# Notes:
# - If run on the host, this script prefers the Dev Containers CLI
#   (`devcontainer exec --workspace-folder <repo> duckdb ...`).
# - If already inside the Dev Container, it runs `duckdb` directly.
# - If neither condition is met and `duckdb` is not on PATH, it
#   prints a helpful message and exits.

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

in_container=false
if [[ -d "/workspaces" ]] || [[ -n "${DEVCONTAINER:-}" ]] || [[ -f "/.dockerenv" ]]; then
  in_container=true
fi

if $in_container; then
  # Inside dev container
  exec duckdb "$@"
fi

if have_cmd devcontainer; then
  # On host with Dev Containers CLI
  exec devcontainer exec --workspace-folder "$ROOT_DIR" duckdb "$@"
fi

# Fallback: try host duckdb if present
if have_cmd duckdb; then
  echo "[warn] Running duckdb on host (devcontainer CLI not found)." >&2
  exec duckdb "$@"
fi

echo "Error: Not inside Dev Container and 'devcontainer' CLI not found.\n" \
     "- Reopen the repo in the Dev Container and re-run this script, or\n" \
     "- Install the Dev Containers CLI: https://github.com/devcontainers/cli" >&2
exit 1

