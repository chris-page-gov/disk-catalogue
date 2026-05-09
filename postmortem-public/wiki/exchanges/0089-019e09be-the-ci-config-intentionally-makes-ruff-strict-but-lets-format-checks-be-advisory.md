---
type: "exchange"
exchange_id: "0089-019e09be-the-ci-config-intentionally-makes-ruff-strict-but-lets-format-checks-be-advisory"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "89"
timestamp: "2026-05-08T22:44:39.431Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont"
turn_position: "assistant-answer"
phase: "Other"
topics:
  - "Release and CI"
entities: []
artifacts:
  - "CI/script"
  - "lint/type"
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/other"
  - "topic/release-ci"
---
# Exchange 89: The CI config intentionally makes Ruff strict but lets format checks be advisory

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) > [Other](../phases/other.md) > Exchange `89`

Global: [Previous exchange](0078-019e09be-the-tests-pass-with-one-expected-looking-skip-the-sample-query-test-skips-becau.md) | [Next exchange](0094-019e09be-uv-regenerated-uv-lock-during-lint-i-ll-remove-it-again-the-working-tree-o.md)
Session: [Previous in session](0078-019e09be-the-tests-pass-with-one-expected-looking-skip-the-sample-query-test-skips-becau.md) | [Next in session](0094-019e09be-uv-regenerated-uv-lock-during-lint-i-ll-remove-it-again-the-working-tree-o.md)

## Surrogate

- Title: The CI config intentionally makes Ruff strict but lets format checks be advisory
- Exchange ID: `0089-019e09be-the-ci-config-intentionally-makes-ruff-strict-but-lets-format-checks-be-advisory`
- Turn: [Turn 2](../turns/turn-0002-019e09be-review-this-repo-and-its-guiding-documents-like-readme-changelog-agents-cont.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-08T22:44:39.431Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Other](../phases/other.md)
- Topics: [Release and CI](../topics/release-ci.md)
- Entities: None
- Artifacts: [CI/script](../artifacts/ci-script.md), [lint/type](../artifacts/lint-type.md)
- Excerpt: The CI config intentionally makes Ruff strict but lets format checks be advisory (|| true for Ruff format and Black in CI/script). I’ll run the local lint/type helper once, so the status covers tests plus static checks.

## Redacted Detail

The raw source transcript is private-only.

The CI config intentionally makes Ruff strict but lets format checks be advisory (\`|| true\` for Ruff format and Black in CI/script). I’ll run the local lint/type helper once, so the status covers tests plus static checks.
