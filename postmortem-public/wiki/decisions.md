# Decision Register

## D001: Use the disk catalogue database as the source of truth.

- Rationale: The database already had stable drive/file identifiers and scan history.
- Outcome: All recovery, transcript, duplicate, and rename artefacts were tied back to DuckDB.

## D002: Copy recovered M4A files to an external SSD before semantic processing.

- Rationale: The source drive could then be ejected and the long-running process could continue.
- Outcome: Later work proceeded without the Ext-10 source drive attached.

## D003: Keep long-running transcription resumable and checkpointed.

- Rationale: The library contained 1,536 files and unattended completion required status checks.
- Outcome: State, logs, verification exports, and evaluation exports were generated.

## D004: Add completeness and duplicate validation before declaring completion.

- Rationale: Partial transcripts and folder-level duplication were explicit user concerns.
- Outcome: Duration coverage and duplicate-audit outputs became part of final verification.

## D005: Use pyannote locally for diarization experiments.

- Rationale: The user wanted local speaker recognition with a small known speaker set.
- Outcome: Sample diarization tables and an effectiveness report were created in the local database.

## D006: Publish `v1.0.0` after merging the semantic catalogue branch to `main`.

- Rationale: The project had crossed from scanning utility into full recovery/catalogue workflow.
- Outcome: The GitHub release workflow published wheel and source assets for `v1.0.0`.

## D007: Keep full assistant transcripts private and publish a redacted derivative.

- Rationale: Raw sessions contain local paths, account state, and generated operational details.
- Outcome: The full archive is ignored in `postmortem/`; `postmortem-public/` is publishable.

## D008: Treat Markdown rendering compatibility as a publication quality gate.

- Rationale: Obsidian and VS Code exposed broken table links, raw HTML folding, flattened redacted details, and filename-like headings that made the archive hard to use.
- Outcome: The generator now emits standard Markdown links, turn pages, escaped public detail, meaningful headings, and publication lint checks for those regressions.
