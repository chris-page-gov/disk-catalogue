---
type: "exchange"
exchange_id: "0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "453"
timestamp: "2026-05-09T00:06:56.122Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0013-019e09be-can-t-it-use-the-apple-gpu"
turn_position: "assistant-answer"
phase: "Speaker Diarization"
topics:
  - "Diarization"
  - "Release and CI"
entities:
  - "pyannote.audio"
artifacts:
  - "pipeline/model"
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/speaker-diarization"
  - "topic/diarization"
  - "topic/release-ci"
---
# Exchange 453: Yes, on Apple Silicon it should be able to use PyTorch’s mps backend, but pyan

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 13](../turns/turn-0013-019e09be-can-t-it-use-the-apple-gpu.md) > [Speaker Diarization](../phases/speaker-diarization.md) > Exchange `453`

Global: [Previous exchange](0452-019e09be-can-t-it-use-the-apple-gpu.md) | [Next exchange](0464-019e09be-mps-is-available-and-the-pyannote-pipeline-exposes-to-so-i-m-going-to-u.md)
Session: [Previous in session](0452-019e09be-can-t-it-use-the-apple-gpu.md) | [Next in session](0464-019e09be-mps-is-available-and-the-pyannote-pipeline-exposes-to-so-i-m-going-to-u.md)

## Surrogate

- Title: Yes, on Apple Silicon it should be able to use PyTorch’s mps backend, but pyan
- Exchange ID: `0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan`
- Turn: [Turn 13](../turns/turn-0013-019e09be-can-t-it-use-the-apple-gpu.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-09T00:06:56.122Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Speaker Diarization](../phases/speaker-diarization.md)
- Topics: [Diarization](../topics/diarization.md), [Release and CI](../topics/release-ci.md)
- Entities: [pyannote.audio](../entities/pyannote-audio.md)
- Artifacts: [pipeline/model](../artifacts/pipeline-model.md)
- Excerpt: Yes, on Apple Silicon it should be able to use PyTorch’s mps backend, but pyannote defaults to CPU unless we explicitly move the pipeline/model to that device. I’m stopping the CPU run and checking MPS support before rerunning the sample.

## Redacted Detail

The raw source transcript is private-only.

Yes, on Apple Silicon it should be able to use PyTorch’s \`mps\` backend, but pyannote defaults to CPU unless we explicitly move the pipeline/model to that device. I’m stopping the CPU run and checking MPS support before rerunning the sample.
