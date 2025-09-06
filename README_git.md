# Git Hygiene

This repository includes a baseline Git setup:

- `.gitignore` covers Python artefacts, macOS metadata, editor state, DuckDB database, large CSV outputs.
- `.gitattributes` normalizes line endings (LF) and marks media formats as binary.
- `commit-template.txt` for Conventional Commit style messages.

## Suggested Local Configuration

Enable the commit template:

```bash
git config commit.template commit-template.txt
```

(Optionally add `--global` to apply across repositories.)

## Branching Model

Use short-lived feature branches named by type:

- `feat/ingest-batch-tracking`
- `fix/scan-script-permissions`
- `chore/ci-workflow`

## Recommended Hooks (Optional)

Add a `.git/hooks/pre-commit` (not committed by default) with:

```bash
#!/usr/bin/env bash
set -euo pipefail
ruff check .
black --check .
mypy .
pytest -q
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

## Next CI Step

Add a GitHub Actions workflow to run lint + type check + tests on push / PR.
