---
type: "artifact"
title: "Artifact: pipeline/model"
exchange_count: "1"
---

# Artifact: pipeline/model

Up: [Navigation](../navigation.md)

| # | Exchange | Turn | Session | Role / kind | Excerpt |
| ---: | --- | --- | --- | --- | --- |
| 453 | [Yes, on Apple Silicon it should be able to use PyTor...](../exchanges/0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan.md) | [Turn 13](../turns/turn-0013-019e09be-can-t-it-use-the-apple-gpu.md) | [019e09be](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md) | assistant / assistant-message | Yes, on Apple Silicon it should be able to use PyTorch’s mps backend, but pyannote defaults to CPU unless we explicitly move the pipeline/model to that device. I’m stopping the CPU run and checking MPS support before rerunning the sample. |
