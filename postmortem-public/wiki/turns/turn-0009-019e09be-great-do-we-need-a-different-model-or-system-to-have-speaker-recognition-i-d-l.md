---
type: "turn"
turn_id: "turn-0009-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
title: "Great, do we need a different model or system to have speaker recognition? I'd l"
exchange_count: "4"
---

# Turn 9: Great, do we need a different model or system to have speaker recognition? I'd l

Up: [Turn Index](index.md)

Session: [019e09be](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md)

| # | Position | Role / kind | Exchange | Excerpt |
| ---: | --- | --- | --- | --- |
| 368 | user-prompt | user / user-message | [Great, do we need a different model or system to hav...](../exchanges/0368-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l.md) | Great, do we need a different model or system to have speaker recognition? I'd like to have the speakers identified as there are only a small number of people in the recordings |
| 369 | user-prompt-copy | user / user-message | [Great, do we need a different model or system to hav...](../exchanges/0369-019e09be-great-do-we-need-a-different-model-or-system-to-have-speaker-recognition-i-d-l.md) | Great, do we need a different model or system to have speaker recognition? I'd like to have the speakers identified as there are only a small number of people in the recordings |
| 370 | assistant-answer | assistant / assistant-message | [I’ll separate two problems: speaker diarization (“sp...](../exchanges/0370-019e09be-i-ll-separate-two-problems-speaker-diarization-speaker-a-b-c-spoke-here-and.md) | I’ll separate two problems: speaker diarization (“speaker A/B/C spoke here”) and speaker identification (“this is Avery Willis”). I’ll check current tooling options briefly, then map that onto your small fixed-speaker audio set. |
| 371 | assistant-answer | assistant / assistant-message | [Yes. Whisper gives transcription; it does **not** re...](../exchanges/0371-019e09be-yes-whisper-gives-transcription-it-does-not-reliably-identify-speakers-by.md) | Yes. Whisper gives transcription; it does **not** reliably identify speakers by name. For what you want, we need a speaker diarization / speaker embedding layer. There are two separate jobs: 1. **Diarization**: “who spoke when?” Output: SPEAKER_00, SPEAKER_01, etc. 2. **Identi... |
