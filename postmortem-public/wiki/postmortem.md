# Postmortem: Following Jesus Catalogue to v1.0.0

## Executive Summary

The project moved from a general disk catalogue into a complete, reproducible workflow for
recovering, transcribing, semantically cataloguing, validating, and renaming the Following
Jesus audio library. The `v1.0.0` release was published successfully, with the GitHub release
workflow creating both wheel and source assets.

Release: [`v1.0.0`](https://github.com/chris-page-gov/disk-catalogue/releases/tag/v1.0.0)

Current post-release head reviewed for this postmortem: [`28df52f`](https://github.com/chris-page-gov/disk-catalogue/commit/28df52fd27f7b7767b614cd9bdd8289e92e29130)

## What Happened

The user first asked for a repository review and then narrowed the work to an old Avery
Willis / Progressive Vision Following Jesus audio library. The workflow discovered the
primary iTunes material, copied the recovered files to external SSD storage, extracted
source metadata, sampled and then expanded transcription, experimented with local
speaker diarization, added completeness and duplicate checks, generated a human-readable
rename scheme, and finally published version `1.0.0`.

After the release, CI exposed an alignment issue: the GitHub workflow still ran `mypy .`
while the local lint script used configured package targets. PR [#1](https://github.com/chris-page-gov/disk-catalogue/pull/1) fixed that
and added the postmortem skill now used to generate this archive.

## Impact

- `1,536` M4A source files were treated as the target Following Jesus corpus.
- The source drive was no longer needed after the copy, reducing operational risk.
- The database became the durable catalogue for embedded metadata, transcripts,
  semantic summaries, verification, duplicate audits, evaluation, and rename planning.
- The public repository now has release artifacts and a reproducible postmortem workflow.

## What Went Well

- The work stayed anchored in the existing DuckDB-backed catalogue rather than creating a
  separate unmanaged inventory.
- The long-running transcription path was made resumable, with status and verification files.
- User concerns about partial transcripts and duplicates were converted into automated
  validation requirements before completion.
- Release publication was verified through GitHub Actions and the release assets were checked.
- The postmortem skill itself was reviewed, adjusted, merged, and then used here.
- Obsidian and VS Code rendering failures were converted into explicit generator behavior,
  skill guidance, and regression tests.

## What Went Wrong

- The first release attempt exposed a CI/local mismatch around `mypy`, even though local
  release checks passed.
- Some generated recovery tooling lived in ignored output space, which is useful locally but
  makes reconstruction dependent on the private archive and database exports.
- Speaker recognition remained experimental: pyannote diarization was useful for samples, but
  the process still needs a stronger reviewed voice-reference library before being treated as
  authoritative metadata.
- Documentation drift existed after release: the README version string still lagged the
  package version until this postmortem pass.
- The first public wiki was not navigable enough: exchange nodes were too isolated, table
  wikilinks split across columns, raw HTML folding showed literal tags, redacted detail was
  flattened into generic code blocks, and opaque filenames were repeated as headings.

## Detection

The key quality signals were explicit user prompts and local verification:

- status checks for the unattended semantic catalogue process
- transcript duration verification to catch early-stopped transcripts
- duplicate-audit exports for exact audio duplicates and repeated album-folder sequences
- `scripts/lint.sh`, `scripts/run_tests.sh`, and schema validation before release
- GitHub Actions release and CI runs after pushing

## Root Causes

- The repository evolved quickly from scanner into recovery pipeline, so local scripts,
  CI, generated outputs, documentation, and release process had to be aligned in a short
  window.
- The project had multiple evidence classes with different publication rules: tracked source,
  ignored generated outputs, local database content, raw assistant transcripts, and external
  SSD media.
- The audio domain needs richer verification than ordinary code tests because success
  depends on full-duration media processing and cataloguing quality, not just executable code.

## Corrective Actions

| Action | Status |
| --- | --- |
| Align CI mypy invocation with local lint config | Done in PR #1 |
| Keep private postmortem archive ignored | Done via `/postmortem/` ignore rule |
| Add rebuildable public/private postmortem generator | Done |
| Add publication lint for local paths, token-like strings, and rendering regressions | Done |
| Replace aliased wikilinks with table-safe Markdown links | Done |
| Add turn pages, surrogate catalogue, graph/facet registers, and structural context | Done |
| Replace raw HTML folding and generic redacted-detail code blocks with portable Markdown | Done |
| Escape public titles and excerpts so placeholders such as `[REPO]` render as text | Done |
| Update README version after `v1.0.0` | Done in this postmortem pass |
| Treat speaker IDs as provisional until reviewed references exist | Open |
| Keep generated recovery outputs documented and exportable from DuckDB | Open |

## Residual Risk

The semantic catalogue is operationally useful, but catalogue quality still depends on
transcription accuracy and final human review of speaker identities, Bible passages, and
storying roles. The postmortem also marks local-only evidence explicitly because the raw
database, generated transcripts, and recovered audio cannot safely be published wholesale.
