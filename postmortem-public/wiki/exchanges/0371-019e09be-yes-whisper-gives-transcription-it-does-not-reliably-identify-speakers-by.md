---
type: "exchange"
exchange_id: "0371-019e09be-yes-whisper-gives-transcription-it-does-not-reliably-identify-speakers-by"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
ordinal: "371"
timestamp: "2026-05-08T23:51:15.687Z"
role: "assistant"
kind: "assistant-message"
turn_id: "turn-0009-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l"
turn_position: "assistant-answer"
phase: "Material Discovery"
topics:
  - "Following Jesus"
  - "Metadata"
  - "Transcription"
  - "Diarization"
  - "Rename Plan"
  - "Release and CI"
entities:
  - "Avery Willis"
  - "pyannote.audio"
  - "whisper.cpp"
artifacts:
  - "huggingface.co/pyannote/speaker-diarization"
  - "huggingface.co/pyannote/embedding"
  - "docs.pyannote.ai/tutorials/identification-with-voiceprints"
  - "known/unknown"
  - "embedding/voiceprint"
  - "start/end"
  - "Avery/Jim/Grant"
tags:
  - "postmortem/exchange"
  - "role/assistant"
  - "kind/assistant-message"
  - "phase/material-discovery"
  - "topic/following-jesus"
  - "topic/metadata"
  - "topic/transcription"
  - "topic/diarization"
  - "topic/rename-plan"
  - "topic/release-ci"
---
# Exchange 371: Yes. Whisper gives transcription; it does **not** reliably identify speakers by

## Structural Context

[Index](../index.md) > [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) > [Turn 9](../turns/turn-0009-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l.md) > [Material Discovery](../phases/material-discovery.md) > Exchange `371`

Global: [Previous exchange](0370-019e09be-i-ll-separate-two-problems-speaker-diarization-speaker-a-b-c-spoke-here-and.md) | [Next exchange](0372-019e09be-compare-this-to-using-davinci-resolve-to-do-this.md)
Session: [Previous in session](0370-019e09be-i-ll-separate-two-problems-speaker-diarization-speaker-a-b-c-spoke-here-and.md) | [Next in session](0372-019e09be-compare-this-to-using-davinci-resolve-to-do-this.md)

## Surrogate

- Title: Yes. Whisper gives transcription; it does **not** reliably identify speakers by
- Exchange ID: `0371-019e09be-yes-whisper-gives-transcription-it-does-not-reliably-identify-speakers-by`
- Turn: [Turn 9](../turns/turn-0009-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l.md) (assistant-answer)
- Session: [Session](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) `019e09be-f0e7-7211-a66f-d0a174cc4534` (Review repo context)
- Timestamp: `2026-05-08T23:51:15.687Z`
- Role / kind: [assistant](../roles/assistant.md) / [assistant-message](../kinds/assistant-message.md)
- Phase: [Material Discovery](../phases/material-discovery.md)
- Topics: [Following Jesus](../topics/following-jesus.md), [Metadata](../topics/metadata.md), [Transcription](../topics/transcription.md), [Diarization](../topics/diarization.md), [Rename Plan](../topics/rename-plan.md), [Release and CI](../topics/release-ci.md)
- Entities: [Avery Willis](../entities/avery-willis.md), [pyannote.audio](../entities/pyannote-audio.md), [whisper.cpp](../entities/whisper-cpp.md)
- Artifacts: [huggingface.co/pyannote/speaker-diarization](../artifacts/huggingface-co-pyannote-speaker-diarization.md), [huggingface.co/pyannote/embedding](../artifacts/huggingface-co-pyannote-embedding.md), [docs.pyannote.ai/tutorials/identification-with-voice...](../artifacts/docs-pyannote-ai-tutorials-identification-with-voiceprints.md), [known/unknown](../artifacts/known-unknown.md), [embedding/voiceprint](../artifacts/embedding-voiceprint.md), [start/end](../artifacts/start-end.md), [Avery/Jim/Grant](../artifacts/avery-jim-grant.md)
- Excerpt: Yes. Whisper gives transcription; it does **not** reliably identify speakers by name. For what you want, we need a speaker diarization / speaker embedding layer. There are two separate jobs: 1. **Diarization**: “who spoke when?” Output: SPEAKER_00, SPEAKER_01, etc. 2. **Identi...

## Redacted Detail

The raw source transcript is private-only.

Yes. Whisper gives transcription; it does **not** reliably identify speakers by name. For what you want, we need a speaker diarization / speaker embedding layer.

There are two separate jobs:

\1. **Diarization**: “who spoke when?”
   Output: \`SPEAKER_00\`, \`SPEAKER_01\`, etc.

\2. **Identification**: “which real person is SPEAKER_00?”
   Output: \`Avery Willis\`, \`Jim Slack\`, \`Grant Lovejoy\`, \`unknown narrator 1\`, etc.

The current \`whisper-cpp\` setup can transcribe, but it is not the right system for robust named speaker recognition. Its \`tinydiarize\` capability is limited and does not solve speaker identity.

Best practical path for this archive:

\- Use **pyannote.audio** locally for diarization and speaker embeddings. Its diarization model can constrain known speaker counts, and its embedding model can compare voice samples by cosine distance. See pyannote speaker diarization and pyannote embedding.
\- Build a small **voice reference library** from known tracks:
  \- \`Avery's Welcome\` is a good Avery seed.
  \- \`Wake Up To Orality And Literacy\` has transcript cues like “Avery, can you respond?”, “Jim Slack…”, and “Grant Lovejoy…”, so we can clip 15-30 second clean single-speaker samples for those voices.
  \- Other recurring narrators can initially be labelled \`unknown_narrator_01\`, etc., then named later.
\- Run diarization across tracks, assign speaker labels by matching segment embeddings to the reference voices, and store confidence scores.

Cloud alternative: **pyannoteAI Precision-2** supports diarization plus voiceprint speaker identification directly. Their docs distinguish diarization from identification and describe voiceprints: pyannoteAI voiceprints. That is likely easier and more accurate, but it means uploading audio.

For this project, I’d add these DB tables next:

\- \`audio_speakers\`: known/unknown speaker identities.
\- \`audio_speaker_voiceprints\`: source clip, embedding/voiceprint metadata, confidence.
\- \`audio_diarization_segments\`: file key, start/end, diarized speaker label.
...
