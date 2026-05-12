# Disk Catalogue

[![CI](https://github.com/chris-page-gov/disk-catalogue/actions/workflows/ci.yml/badge.svg)](https://github.com/chris-page-gov/disk-catalogue/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chris-page-gov/disk-catalogue?sort=semver)](https://github.com/chris-page-gov/disk-catalogue/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](pyproject.toml)

Version: 1.0.0


Early-stage toolkit for scanning mounted volumes and exploring metadata (paths, sizes) via DuckDB.

## Quick Start (Dev Container)

1. Open repository in VS Code.
2. Reopen in container when prompted.
3. (Optional) Install dependencies editable: `uv pip install -e .[dev]` or `pip install -e .[dev]`.
4. Run tests: `pytest`.
5. Lint/format/type-check:
   - Quick: `scripts/lint.sh`
   - Auto-fix imports/formatting: `scripts/lint.sh --fix`

### Note on open files after scans

- When running inside the Dev Container, macOS' Virtualization.framework and Spotlight can briefly hold file descriptors on recently scanned files. You may see `lsof` entries for the container VM (Virtualization.framework) or Spotlight (mds/mdworker).
- Mitigations:
  - Stop the Dev Container/VM after scans (VS Code: Dev Containers: Stop Container). This releases virtualization-held FDs.
  - Optionally pause Spotlight on the volume: `sudo mdutil -i off "/Volumes/<Drive>"` and re-enable later.
  - Run scans on the host (outside the container): the tooling now auto-detects environment and will use native `/Volumes/...` when `/host/Volumes` is unavailable.
  - Use ephemeral containers for scanning so the process exits immediately after completing the job.

## Catalogue A Drive

1. Ensure the drive is visible in the container: `ls /host/Volumes/Ext-10`.
2. Create a local manifest (untracked):
   - Copy `drive_manifest.template.csv` to `drive_manifest.csv` and fill values (label, mounts, optional UUID/serial).
   - Note: `drive_manifest.csv` is gitignored to avoid committing machine-specific data.
   - Or bootstrap entries from mounted volumes inside the Dev Container:
     ```bash
     python scripts/make_manifest.py
     ```
3. Run the one-shot scan + ingest:

```bash
python scripts/scan_and_ingest.py --drive Ext-10
```

This writes CSVs under `output/Ext-10/` and ingests them into DuckDB. Re-run later; it skips
already ingested tables for that drive. Use `--force` to rescan.

Output files under `output/` are generated and ignored by Git (entire directory is excluded).

Tip: If the drive label isn’t in your manifest yet, add `--update-manifest`:

```bash
python scripts/scan_and_ingest.py --drive Ext-10 --update-manifest
```

## Views & Identifiers

- Ingestion creates views `files`, `photos`, `videos` with derived columns:
  - `Drive`, `RelativePath`, `RelativeDirectory`, `FileExt`.
  - `FileKey = hash(Drive, RelativePath, FileSize#)` (stable per-file ID on a drive).
- Example:

```bash
scripts/run_sql.sh catalogue.duckdb -c "select Drive, RelativePath, FileExt, \"FileSize#\" from files limit 10;"
```

## Duplicates 101

- By size only (broad candidates):
```bash
scripts/run_sql.sh catalogue.duckdb -c "select \"FileSize#\" bytes, count(*) n, count(distinct Drive) drives from files group by 1 having n>1 order by n desc, bytes desc limit 50;"
```
- By name + size (stronger):
```bash
scripts/run_sql.sh catalogue.duckdb -c "select lower(FileName) name, \"FileSize#\" bytes, count(*) n, list(distinct Drive) drives from files group by 1,2 having n>1 order by n desc, bytes desc limit 50;"
```
- Pairs across drives (same name + size):
```bash
scripts/run_sql.sh catalogue.duckdb -c "select a.Drive a_drive, b.Drive b_drive, a.RelativePath a_path, b.RelativePath b_path, a.\"FileSize#\" bytes from files a join files b on a.\"FileSize#\"=b.\"FileSize#\" and lower(a.FileName)=lower(b.FileName) and a.Drive<b.Drive limit 50;"
```
- Exact match later: add a `file_checksums` table with content hashes (MD5/SHA256) keyed by (Drive, RelativePath, FileSize#), then group by checksum to confirm duplicates precisely.

## Scan Summaries

- Last scan per drive (status + counts): see `sample_queries.sql` section “Scan summaries”.
- Quick run:
```bash
scripts/run_sql.sh catalogue.duckdb -c "WITH r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY drive_label ORDER BY started_at DESC) rn FROM drive_scans) SELECT drive_label, started_at, ended_at, status, files_rows, photos_rows, videos_rows, (epoch(ended_at) - epoch(started_at)) AS duration_s FROM r WHERE rn=1 ORDER BY drive_label;"
```

## Following Jesus Semantic Audio Catalogue

The recovery workflow for the Following Jesus audio set is handled by:

```bash
python scripts/catalogue_following_jesus_semantic.py
```

Default inputs:

- `output/recovery_plans/following_jesus_team_ext10/audio_metadata.csv`
- `output/models/ggml-base.en.bin`
- copied M4A files referenced by `destination_path` in the metadata CSV
- optional gold questions at `eval/following_jesus_gold_questions.json`

Default outputs go under `output/recovery_plans/following_jesus_team_ext10/semantic_catalogue/`:

- `transcripts/<album>/...txt`, `.srt`, and per-file `.semantic.json` sidecars.
- `semantic_catalogue_state.json` for resumability and status.
- `semantic_catalogue.csv`, `semantic_catalogue_source_metadata.csv`,
  `semantic_catalogue_status.csv`,
  `semantic_catalogue_duplicates.csv`, `semantic_catalogue_verification.json`, and optional
  `semantic_catalogue_evaluation.csv`.

The script is resumable. It skips completed files when the source size and mtime are unchanged,
writes status after each file, checkpoints exports every `--checkpoint-interval` files, and
continues after individual file failures. Use:

```bash
python scripts/catalogue_following_jesus_semantic.py --status
python scripts/catalogue_following_jesus_semantic.py --verify
python scripts/catalogue_following_jesus_semantic.py --evaluate
python scripts/catalogue_following_jesus_semantic.py --retry-failed
python scripts/catalogue_following_jesus_semantic.py --force
```

DuckDB tables written to `catalogue.duckdb`:

- `audio_semantic_catalogue`: one row per catalogued track with semantic title, type,
  Bible reference/book, speakers, storying role, summaries, keywords, transcript paths,
  confidence, evidence JSON, and analysis backend.
- `audio_semantic_source_metadata`: the full source metadata CSV rows, preserving all extracted
  embedded-tag fields and raw `metadata_json` for later re-analysis.
- `audio_semantic_catalogue_status`: per-file processing state, source fingerprint,
  transcript/sidecar paths, elapsed time, failures, and latest inferred metadata.
- `audio_semantic_catalogue_duplicates`: exact SHA-256 duplicate groups and duplicated
  album-folder sequence groups found during final verification.
- `audio_semantic_catalogue_verification`: one-row completeness check covering expected files,
  catalogued files, transcript files, missing catalogue rows, missing transcripts, empty
  transcripts, SRT end-time checks for transcripts that stop before the source audio ends,
  and whether the duplicate audit has run.
- `audio_semantic_catalogue_eval`: optional gold-question scores with pass/fail and details JSON.

See `sample_queries.sql` for semantic catalogue status, verification, evaluation, and search
examples.

## Following Jesus Rename Plan

Use the semantic catalogue database to generate a readable, reversible rename plan without changing
files:

```bash
python scripts/plan_following_jesus_rename.py
python scripts/validate_following_jesus_rename.py --mode before
python scripts/rename_following_jesus_files.py
```

The naming scheme is:

- module folder: `FJ-M03 Living in the Family`
- disc folder: `Disc 02`
- file name: `FJ-M03-D02-T09 - Jesus Calls the First Disciples.m4a`

`scripts/rename_following_jesus_files.py` is dry-run by default. Use `--apply` only after
reviewing the generated plan and validation report.

## Assistant Postmortem

The assistant-collaboration postmortem uses the repository-local skill at
`skills/assistant-postmortem-wiki/SKILL.md` and is regenerated with:

```bash
python tools/build_assistant_postmortem.py
```

This writes two outputs:

- `postmortem/`: private local archive with raw Codex session sources and full exchange notes.
  This path is gitignored.
- `postmortem-public/`: redacted public wiki with summaries, decision registers, artifact
  registers, and publication lint results.

The generated wikis use standard Markdown links so they render in native VS Code previews while
remaining valid Obsidian internal links. Exchange notes link to previous/next exchanges, sessions,
phases, topics, entities, artifacts, roles, and kinds. They also include surrogate-to-detail
sections, user-prompt to assistant-answer turn pages, timeline and surrogate catalogue pages, and
machine-readable `graph_nodes.json`, `graph_edges.json`, `facets.json`, and `turns.json`
registers.

## Run SQL (container‑friendly)

- Use the helper to run the DuckDB CLI inside the Dev Container (or on host if already inside):
  - Interactive: `scripts/run_sql.sh catalogue.duckdb`
  - One‑liner: `scripts/run_sql.sh catalogue.duckdb -c 'SELECT 1;'`
- Works with `sample_queries.sql`. Example — Top cameras and lenses:
  - `scripts/run_sql.sh catalogue.duckdb -c "SELECT Model, LensModel, COUNT(*) AS n FROM photos GROUP BY 1,2 ORDER BY n DESC LIMIT 25;"`
- If run on host without the Dev Containers CLI installed, it warns and falls back to host `duckdb` if available; otherwise it prints setup instructions.
- Or via a friendly CLI table:
```bash
python scripts/scan_summary.py --db catalogue.duckdb
# CSV output:
python scripts/scan_summary.py --db catalogue.duckdb --csv > last_scans.csv
```

## Features (initial)

- Recursive file scanning
- Returns structured `FileRecord` objects
- TDD scaffold (pytest, coverage, mypy, ruff, black)

## Roadmap

See `CHANGELOG.md` and `COPILOT_INSTRUCTIONS.md` for future ideas.

## License

MIT
