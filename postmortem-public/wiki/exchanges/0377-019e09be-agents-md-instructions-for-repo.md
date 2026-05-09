---
type: "exchange"
exchange_id: "0377-019e09be-agents-md-instructions-for-repo"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "377"
timestamp: "2026-05-09T00:00:35.489Z"
role: "user"
kind: "user-message"
turn_id: "turn-0011-019e09be-agents-md-instructions-for-repo"
turn_position: "user-prompt"
phase: "Repo Orientation"
topics:
  - "Repo Review"
  - "Disk Catalogue"
  - "Drive Recovery"
  - "Verification"
  - "Rename Plan"
  - "Release and CI"
  - "Security"
entities:
  - "DuckDB"
  - "GitHub"
  - "GitHub Actions"
artifacts:
  - "src/disk_catalogue/"
  - "tests/"
  - "test_*.py"
  - "scripts/"
  - "output/"
  - "duckdb_schema.sql"
  - "sample_queries.sql"
  - "drive_manifest.csv"
  - "pip install -e .\\[dev\\]"
  - "uv pip install -e .\\[dev\\]"
  - "scripts/run_tests.sh"
  - "scripts/lint.sh"
  - "ruff format "
  - "black "
  - "src/"
  - "pyproject.toml"
  - "commit-template.txt"
  - "CHANGELOG.md"
  - "README.md"
  - "README_cataloguing.md"
tags:
  - "postmortem/exchange"
  - "role/user"
  - "kind/user-message"
  - "phase/repo-orientation"
  - "topic/repo-review"
  - "topic/disk-catalogue"
  - "topic/drive-recovery"
  - "topic/verification"
  - "topic/rename-plan"
  - "topic/release-ci"
  - "topic/security"
---
# Exchange 377: AGENTS.md instructions for \[REPO\]

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 11](../turns/turn-0011-019e09be-agents-md-instructions-for-repo.md) > [Repo Orientation](../phases/repo-orientation.md) > Exchange `377`

Global: [Previous exchange](0375-019e09be-resolve-is-useful-here-but-i-would-not-make-it-the-primary-cataloguing-system.md) | [Next exchange](0378-019e09be-use-pyannote-audio-locally-for-diarization-and-speaker-embeddings.md)
Session: [Previous in session](0375-019e09be-resolve-is-useful-here-but-i-would-not-make-it-the-primary-cataloguing-system.md) | [Next in session](0378-019e09be-use-pyannote-audio-locally-for-diarization-and-speaker-embeddings.md)

## Surrogate

- Title: AGENTS.md instructions for \[REPO\]
- Exchange ID: `0377-019e09be-agents-md-instructions-for-repo`
- Turn: [Turn 11](../turns/turn-0011-019e09be-agents-md-instructions-for-repo.md) (user-prompt)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-09T00:00:35.489Z`
- Role / kind: [user](../roles/user.md) / [user-message](../kinds/user-message.md)
- Phase: [Repo Orientation](../phases/repo-orientation.md)
- Topics: [Repo Review](../topics/repo-review.md), [Disk Catalogue](../topics/disk-catalogue.md), [Drive Recovery](../topics/drive-recovery.md), [Verification](../topics/verification.md), [Rename Plan](../topics/rename-plan.md), [Release and CI](../topics/release-ci.md), [Security](../topics/security.md)
- Entities: [DuckDB](../entities/duckdb.md), [GitHub](../entities/github.md), [GitHub Actions](../entities/github-actions.md)
- Artifacts: [src/disk_catalogue/](../artifacts/src-disk-catalogue.md), [tests/](../artifacts/tests.md), [test_*.py](../artifacts/test-py.md), [scripts/](../artifacts/scripts.md), [output/](../artifacts/output.md), [duckdb_schema.sql](../artifacts/duckdb-schema-sql.md), [sample_queries.sql](../artifacts/sample-queries-sql.md), [drive_manifest.csv](../artifacts/drive-manifest-csv.md), [pip install -e .(dev)](../artifacts/pip-install-e-dev.md), [uv pip install -e .(dev)](../artifacts/uv-pip-install-e-dev.md), [scripts/run_tests.sh](../artifacts/scripts-run-tests-sh.md), [scripts/lint.sh](../artifacts/scripts-lint-sh.md), [ruff format](../artifacts/ruff-format.md), [black](../artifacts/black.md), [src/](../artifacts/src.md), [pyproject.toml](../artifacts/pyproject-toml.md), [commit-template.txt](../artifacts/commit-template-txt.md), [CHANGELOG.md](../artifacts/changelog-md.md), [README.md](../artifacts/readme-md.md), [README_cataloguing.md](../artifacts/readme-cataloguing-md.md)
- Excerpt: AGENTS.md instructions for \[REPO\] Repository Guidelines Project Structure & Module Organization src/disk_catalogue/: Python package (scanner and public API). tests/: Pytest suite (test_*.py). scripts/: Dev and data tooling (lint, tests, CSV/DuckDB helpers). output/: Generated...

## Redacted Detail

The raw source transcript is private-only.

\# AGENTS.md instructions for \[REPO\]

&lt;INSTRUCTIONS&gt;
\# Repository Guidelines

\## Project Structure & Module Organization
\- \`src/disk_catalogue/\`: Python package (scanner and public API).
\- \`tests/\`: Pytest suite (\`test_*.py\`).
\- \`scripts/\`: Dev and data tooling (lint, tests, CSV/DuckDB helpers).
\- \`output/\`: Generated CSVs from drive scans (gitignored).
\- Root SQL/CSV docs: \`duckdb_schema.sql\`, \`sample_queries.sql\`, \`drive_manifest.csv\`.

\## Build, Test, and Development Commands
\- Install (editable, with dev tools): \`pip install -e .\[dev\]\` (or \`uv pip install -e .\[dev\]\`).
\- Run tests (with coverage via pyproject): \`pytest\` or \`scripts/run_tests.sh\`.
\- Lint/format/type-check: \`scripts/lint.sh\` (runs ruff, black --check, mypy).
\- Format code: \`ruff format .\` (or \`black .\`).

\## Coding Style & Naming Conventions
\- Python 3.11, 4‑space indent, LF endings; max line length 100.
\- Use \`ruff\` (rules: E,F,W,I,B,C4,UP,RUF) and \`black\` for formatting.
\- Types: \`mypy --strict\` is enabled; add/maintain type hints.
\- Naming: modules and functions \`snake_case\`, classes \`PascalCase\`, constants \`UPPER_SNAKE_CASE\`.
\- Package import path is \`disk_catalogue\` (ensure code lives under \`src/\`).

\## Testing Guidelines
\- Framework: \`pytest\` with \`pytest-cov\` (configured in \`pyproject.toml\`).
\- Name tests \`test_*.py\`; prefer small, deterministic unit tests.
\- Keep/raise coverage when changing behavior; add tests for regressions.
\- Use \`tmp_path\` and fixtures for filesystem interactions.

\## Commit & Pull Request Guidelines
\- Follow Conventional Commits (see \`commit-template.txt\`): \`type(scope): subject\`.
  Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci.
\- PRs: include clear description, linked issues, and before/after notes. For data/CLI changes, show example command/output.
\- Run \`scripts/lint.sh\` and \`pytest\` locally before opening a PR.

\## Docs & Changelog Sync
\- Always update \`CHANGELOG.md\` (Unreleased) for user-visible changes: new scripts/CLI flags, schema/view changes, devcontainer behavior, or Git ignore patterns.
\- Keep docs current when code changes:
  \- \`README.md\`: quick start, catalogue/queries examples, new commands.
  \- \`README_cataloguing.md\`: e
...
