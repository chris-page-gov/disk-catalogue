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

## Continuous Integration (CI)

This repository runs lint, type checks, and tests on every push and pull request.

What runs (see `.github/workflows/ci.yml`):
- Ruff lint (`ruff check .`)
- Ruff format check (`ruff format --check .`)
- Black check (`black --check .`)
- Mypy type checking (`mypy .`)
- Pytest (with coverage flags from `pyproject.toml`)

### Coverage Reporting
- CI produces `coverage.xml` and uploads it as a build artifact.
- View terminal summary in job logs; download `coverage-xml` artifact for detailed inspection or integration with external tools.

Targets Python 3.11 to match the project requirement.

## Releases via CI

This repository publishes releases automatically when you push a tag like `v0.1.2`.

Steps (maintainers):

1. Update code + docs and edit `CHANGELOG.md` under `[Unreleased]`.
2. Bump version in `pyproject.toml` and `src/disk_catalogue/__init__.py`.
3. Finalize the changelog: move items to a new `## [x.y.z] - YYYY-MM-DD` section.
4. Commit and push to `main`:
   ```bash
   git add -A
   git commit -m "chore(release): vX.Y.Z"
   git push
   ```
5. Create and push the tag (triggers the workflow):
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push --tags
   ```

What CI does:
- Builds sdist/wheel under `dist/`.
- Extracts the matching section from `CHANGELOG.md` as release notes.
- Creates a GitHub Release named after the tag and uploads `dist/*`.

Find it under GitHub → Releases.
