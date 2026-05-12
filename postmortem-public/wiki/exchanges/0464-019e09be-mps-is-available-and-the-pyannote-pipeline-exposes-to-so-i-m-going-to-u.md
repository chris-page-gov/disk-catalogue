---
type: "exchange"
exchange_id: "0464-019e09be-mps-is-available-and-the-pyannote-pipeline-exposes-to-so-i-m-going-to-u"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "464"
timestamp: "2026-05-09T00:07:50.627Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0013-019e09be-can-t-it-use-the-apple-gpu"
turn_position: "assistant-answer"
phase: "Speaker Diarization"
topics:
  - "Diarization"
entities:
  - "pyannote.audio"
artifacts:
  - "to("
  - "pipeline.to(torch.device(\"mps\""
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/speaker-diarization"
  - "topic/diarization"
---
# Exchange 464: MPS is available and the pyannote pipeline exposes .to(...), so I’m going to u

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 13](../turns/turn-0013-019e09be-can-t-it-use-the-apple-gpu.md) > [Speaker Diarization](../phases/speaker-diarization.md) > Exchange `464`

Global: [Previous exchange](0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan.md) | End of archive
Session: [Previous in session](0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan.md) | End of session

## Surrogate

- Title: MPS is available and the pyannote pipeline exposes .to(...), so I’m going to u
- Exchange ID: `0464-019e09be-mps-is-available-and-the-pyannote-pipeline-exposes-to-so-i-m-going-to-u`
- Turn: [Turn 13](../turns/turn-0013-019e09be-can-t-it-use-the-apple-gpu.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-09T00:07:50.627Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Speaker Diarization](../phases/speaker-diarization.md)
- Topics: [Diarization](../topics/diarization.md)
- Entities: [pyannote.audio](../entities/pyannote-audio.md)
- Artifacts: [to(](../artifacts/to.md), [pipeline.to(torch.device("mps"](../artifacts/pipeline-to-torch-device-mps.md)
- Excerpt: MPS is available and the pyannote pipeline exposes .to(...), so I’m going to use pipeline.to(torch.device("mps")). The CPU process didn’t accept an interrupt through this shell session, so I’m locating that one process and stopping it before rerunning on the Apple GPU.

## Redacted Detail

The raw source transcript is private-only.

MPS is available and the pyannote pipeline exposes \`.to(...)\`, so I’m going to use \`pipeline.to(torch.device("mps"))\`. The CPU process didn’t accept an interrupt through this shell session, so I’m locating that one process and stopping it before rerunning on the Apple GPU.
