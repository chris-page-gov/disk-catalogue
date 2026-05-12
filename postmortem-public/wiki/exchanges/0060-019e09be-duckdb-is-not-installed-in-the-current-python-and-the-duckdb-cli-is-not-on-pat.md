---
type: "exchange"
exchange_id: "0060-019e09be-duckdb-is-not-installed-in-the-current-python-and-the-duckdb-cli-is-not-on-pat"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "60"
timestamp: "2026-05-08T22:42:19.539Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont"
turn_position: "assistant-answer"
phase: "Other"
topics:
  - "Disk Catalogue"
entities:
  - "DuckDB"
artifacts: []
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/other"
  - "topic/disk-catalogue"
---
# Exchange 60: duckdb is not installed in the current Python and the DuckDB CLI is not on PAT

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) > [Other](../phases/other.md) > Exchange `60`

Global: [Previous exchange](0049-019e09be-the-local-shell-doesn-t-have-python-on-path-so-i-ll-use-python3-for-the-rea.md) | [Next exchange](0069-019e09be-the-database-has-real-catalogue-state-about-1-1-million-file-rows-across-seven.md)
Session: [Previous in session](0049-019e09be-the-local-shell-doesn-t-have-python-on-path-so-i-ll-use-python3-for-the-rea.md) | [Next in session](0069-019e09be-the-database-has-real-catalogue-state-about-1-1-million-file-rows-across-seven.md)

## Surrogate

- Title: duckdb is not installed in the current Python and the DuckDB CLI is not on PAT
- Exchange ID: `0060-019e09be-duckdb-is-not-installed-in-the-current-python-and-the-duckdb-cli-is-not-on-pat`
- Turn: [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-08T22:42:19.539Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Other](../phases/other.md)
- Topics: [Disk Catalogue](../topics/disk-catalogue.md)
- Entities: [DuckDB](../entities/duckdb.md)
- Artifacts: None
- Excerpt: duckdb is not installed in the current Python and the DuckDB CLI is not on PATH, but uv is available. I’ll try the project environment through uv so I can inspect the database with the declared dependency rather than installing anything manually.

## Redacted Detail

The raw source transcript is private-only.

\`duckdb\` is not installed in the current Python and the DuckDB CLI is not on PATH, but \`uv\` is available. I’ll try the project environment through \`uv\` so I can inspect the database with the declared dependency rather than installing anything manually.
