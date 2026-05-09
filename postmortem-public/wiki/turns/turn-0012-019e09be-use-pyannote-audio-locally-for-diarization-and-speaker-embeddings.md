---
type: "turn"
turn_id: "turn-0012-019e09be-use-pyannote-audio-locally-for-diarization-and-speaker-embeddings"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
title: "Use pyannote.audio locally for diarization and speaker embeddings."
exchange_count: "9"
---

# Turn 12: Use pyannote.audio locally for diarization and speaker embeddings.

Up: [Turn Index](index.md)

Session: [019e09be](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md)

| # | Position | Role / kind | Exchange | Excerpt |
| ---: | --- | --- | --- | --- |
| 378 | user-prompt | user / user-message | [Use pyannote.audio locally for diarization and speak...](../exchanges/0378-019e09be-use-pyannote-audio-locally-for-diarization-and-speaker-embeddings.md) | Use pyannote.audio locally for diarization and speaker embeddings. Test this as you suggested by building the voice reference library and then run diarisation across our sample tracks capturing in the databasee and then report on how effective this is |
| 379 | user-prompt-copy | user / user-message | [Use pyannote.audio locally for diarization and speak...](../exchanges/0379-019e09be-use-pyannote-audio-locally-for-diarization-and-speaker-embeddings.md) | Use pyannote.audio locally for diarization and speaker embeddings. Test this as you suggested by building the voice reference library and then run diarisation across our sample tracks capturing in the databasee and then report on how effective this is |
| 380 | assistant-answer | assistant / assistant-message | [I’ll treat this as an end-to-end local experiment: i...](../exchanges/0380-019e09be-i-ll-treat-this-as-an-end-to-end-local-experiment-inspect-the-existing-catalogu.md) | I’ll treat this as an end-to-end local experiment: inspect the existing catalogue tables and sample manifests, add a focused diarization workflow if the repo doesn’t already have one, then run it against the eight sample tracks and write the results back into catalogue.duckdb. |
| 389 | assistant-answer | assistant / assistant-message | [The repo doesn’t currently have diarization code or...](../exchanges/0389-019e09be-the-repo-doesn-t-currently-have-diarization-code-or-speaker-tables-so-i-m-check.md) | The repo doesn’t currently have diarization code or speaker tables, so I’m checking the generated sample manifests and the local Python/audio toolchain before deciding whether this can run fully offline as-is. |
| 406 | assistant-answer | assistant / assistant-message | [The sample set and database are in place. The missin...](../exchanges/0406-019e09be-the-sample-set-and-database-are-in-place-the-missing-piece-is-the-ml-stack-py.md) | The sample set and database are in place. The missing piece is the ML stack: pyannote, torch, torchaudio, and scikit-learn are not installed in the project environment, so I’m checking for an existing Hugging Face token/cache before installing anything. |
| 413 | assistant-answer | assistant / assistant-message | [There is no local Hugging Face token and no cached p...](../exchanges/0413-019e09be-there-is-no-local-hugging-face-token-and-no-cached-pyannote-model-i-ll-install.md) | There is no local Hugging Face token and no cached pyannote model. I’ll install the Python packages first; model loading may still require a Hugging Face token because the standard pyannote diarization and embedding models are gated. |
| 418 | assistant-answer | assistant / assistant-message | [The package stack is now available via `uv run --wit...](../exchanges/0418-019e09be-the-package-stack-is-now-available-via-uv-run-with-next-i-m-checking-wh.md) | The package stack is now available via uv run --with .... Next I’m checking whether the pyannote community pipeline can be loaded locally without credentials; if it can’t, we’ll need to fall back to whatever model access is available or stop at a prepared workflow. |
| 425 | assistant-answer | assistant / assistant-message | [The official pyannote models are gated without a tok...](../exchanges/0425-019e09be-the-official-pyannote-models-are-gated-without-a-token-but-an-openly-accessible.md) | The official pyannote models are gated without a token, but an openly accessible Hugging Face mirror of the community-1 pipeline loaded successfully through pyannote.audio. I’ll use that for the local test and record the model source clearly in the database/report so the prove... |
| 448 | assistant-answer | assistant / assistant-message | [The first diarization run is processing the longest...](../exchanges/0448-019e09be-the-first-diarization-run-is-processing-the-longest-sample-locally-on-cpu-that.md) | The first diarization run is processing the longest sample locally on CPU. That is expected to take a few minutes; the model is running on-device, with no cloud transcription or cloud speaker analysis. |
