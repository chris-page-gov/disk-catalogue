---
type: "exchange"
exchange_id: "0118-019e09be-i-reviewed-the-repo-docs-scripts-schema-notes-current-database-and-checks-n"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "118"
timestamp: "2026-05-08T22:46:17.651Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont"
turn_position: "assistant-answer"
phase: "Repo Orientation"
topics:
  - "Repo Review"
  - "Disk Catalogue"
  - "Drive Recovery"
  - "Metadata"
  - "Release and CI"
entities:
  - "Ext-10"
  - "DuckDB"
artifacts:
  - "drive_manifest.csv"
  - "scripts/scan_and_ingest.py"
  - "output/&lt;drive&gt;/"
  - "catalogue.duckdb"
  - "output/"
  - "files/photos/videos"
  - "origin/main"
  - "0.1.5"
  - "v0.1.5"
  - "scripts/lint.sh"
  - "scripts/generate_schema_reference.py"
  - "typing.Iterable"
  - "README.md"
  - "duckdb_schema.sql"
  - "sample_queries.sql"
  - "SCHEMA_REFERENCE.md"
  - "CSV/list"
  - "snapshot/history"
  - "camera/lens"
  - "file/path/size/media"
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/repo-orientation"
  - "topic/repo-review"
  - "topic/disk-catalogue"
  - "topic/drive-recovery"
  - "topic/metadata"
  - "topic/release-ci"
---
# Exchange 118: I reviewed the repo docs, scripts, schema notes, current database, and checks. N

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) > [Repo Orientation](../phases/repo-orientation.md) > Exchange `118`

Global: [Previous exchange](0113-019e09be-one-workspace-side-effect-remains-uv-created-a-local-venv-for-the-checks.md) | [Next exchange](0119-019e09be-so-i-m-looking-for-an-old-music-library-ripped-from-cd-of-avery-willis-storying.md)
Session: [Previous in session](0113-019e09be-one-workspace-side-effect-remains-uv-created-a-local-venv-for-the-checks.md) | [Next in session](0119-019e09be-so-i-m-looking-for-an-old-music-library-ripped-from-cd-of-avery-willis-storying.md)

## Surrogate

- Title: I reviewed the repo docs, scripts, schema notes, current database, and checks. N
- Exchange ID: `0118-019e09be-i-reviewed-the-repo-docs-scripts-schema-notes-current-database-and-checks-n`
- Turn: [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-08T22:46:17.651Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Repo Orientation](../phases/repo-orientation.md)
- Topics: [Repo Review](../topics/repo-review.md), [Disk Catalogue](../topics/disk-catalogue.md), [Drive Recovery](../topics/drive-recovery.md), [Metadata](../topics/metadata.md), [Release and CI](../topics/release-ci.md)
- Entities: [Ext-10](../entities/ext-10.md), [DuckDB](../entities/duckdb.md)
- Artifacts: [drive_manifest.csv](../artifacts/drive-manifest-csv.md), [scripts/scan_and_ingest.py](../artifacts/scripts-scan-and-ingest-py.md), [output/drive/](../artifacts/output-drive.md), [catalogue.duckdb](../artifacts/catalogue-duckdb.md), [output/](../artifacts/output.md), [files/photos/videos](../artifacts/files-photos-videos.md), [origin/main](../artifacts/origin-main.md), [0.1.5](../artifacts/0-1-5.md), [v0.1.5](../artifacts/v0-1-5.md), [scripts/lint.sh](../artifacts/scripts-lint-sh.md), [scripts/generate_schema_reference.py](../artifacts/scripts-generate-schema-reference-py.md), [typing.Iterable](../artifacts/typing-iterable.md), [README.md](../artifacts/readme-md.md), [duckdb_schema.sql](../artifacts/duckdb-schema-sql.md), [sample_queries.sql](../artifacts/sample-queries-sql.md), [SCHEMA_REFERENCE.md](../artifacts/schema-reference-md.md), [CSV/list](../artifacts/csv-list.md), [snapshot/history](../artifacts/snapshot-history.md), [camera/lens](../artifacts/camera-lens.md), [file/path/size/media](../artifacts/file-path-size-media.md)
- Excerpt: I reviewed the repo docs, scripts, schema notes, current database, and checks. No external-disk scan was attempted. **Where the project is up to** This is an early-stage offline disk catalogue. The current intended workflow is: mount a drive, identify it via drive_manifest.csv...

## Redacted Detail

The raw source transcript is private-only.

I reviewed the repo docs, scripts, schema notes, current database, and checks. No external-disk scan was attempted.

**Where the project is up to**

This is an early-stage offline disk catalogue. The current intended workflow is: mount a drive, identify it via \`drive_manifest.csv\`, run \`scripts/scan_and_ingest.py\`, generate CSVs under \`output/&lt;drive&gt;/\`, ingest them into \`catalogue.duckdb\`, then query the derived \`files\`, \`photos\`, and \`videos\` views by \`Drive\`, \`RelativePath\`, \`FileExt\`, and \`FileKey\`.

Local catalogue state:

\- \`catalogue.duckdb\`: 178 MB
\- \`output/\`: 612 MB of generated scan CSV/list files
\- Database rows:
  \- \`files\`: 1,114,254
  \- \`photos\`: 766,730
  \- \`videos\`: 14,951
\- Indexed drive labels in \`files\`: \`Ext-10\`, \`Ext-11\`, \`Ext-12\`, \`Ext-13\`, \`Ext-14\`, \`Ext-15\`, \`Bethel-Serv\`
\- Manifest also lists \`Ext-16\` and \`Macintosh HD\`, but they are not indexed in the current DB.

Approximate indexed data by drive:

| Drive | Files | TB |
|---|---:|---:|
| \`Ext-12\` | 346,806 | 13.603 |
| \`Ext-10\` | 320,082 | 4.384 |
| \`Ext-13\` | 227,421 | 15.673 |
| \`Ext-14\` | 93,616 | 19.872 |
| \`Ext-11\` | 93,316 | 7.765 |
| \`Ext-15\` | 29,093 | 15.884 |
| \`Bethel-Serv\` | 3,920 | 7.942 |

The scan history is mostly from **September 13-14, 2025**. One data-quality wrinkle: \`Ext-13\` is present in \`files/photos/videos\`, but absent from \`drives\` and \`drive_scans\`, so its CSVs were ingested without the later scan snapshot/history metadata being recorded.

**Repo Health**

\- Git working tree is clean.
\- Current branch: \`main\`, behind \`origin/main\` by 1 commit.
\- Current local version: \`0.1.5\`.
\- Latest local tag: \`v0.1.5\`.
\- Tests: \`3 passed, 1 skipped\`.
\- The skipped test is the sample camera/lens query because the current \`photos\` view lacks \`Model\`/\`LensModel\`; test says to rescan photos with EXIF tags to enable it.

Static checks are not clean right now. \`scripts/lint.sh\` fails at Ruff before mypy runs, mainly in:

\- \`scripts/generate_schema_reference.py\`: import placement, \`typing.Iterable\`, line length, non-ASCII punctuation.
\- \`scripts/scan_and_ingest.py\`: two long lines around hidden-file filtering.

Docs are mostly coherent, but a few things need tidying:

\- \`REA
...
