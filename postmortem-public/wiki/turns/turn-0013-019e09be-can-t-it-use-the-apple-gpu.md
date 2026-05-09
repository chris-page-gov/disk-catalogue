---
type: "turn"
turn_id: "turn-0013-019e09be-can-t-it-use-the-apple-gpu"
session_id: "019e09be-f0e7-7211-a66f-d0a174cc4534"
title: "Can't it use the Apple GPU?"
exchange_count: "4"
---

# Turn 13: Can't it use the Apple GPU?

Up: [Turn Index](index.md)

Session: [019e09be](../sessions/session-019e09be-f0e7-7211-a66f-d0a174cc4534.md)

| # | Position | Role / kind | Exchange | Excerpt |
| ---: | --- | --- | --- | --- |
| 451 | user-prompt | user / user-message | [Can't it use the Apple GPU?](../exchanges/0451-019e09be-can-t-it-use-the-apple-gpu.md) | Can't it use the Apple GPU? |
| 452 | user-prompt-copy | user / user-message | [Can't it use the Apple GPU?](../exchanges/0452-019e09be-can-t-it-use-the-apple-gpu.md) | Can't it use the Apple GPU? |
| 453 | assistant-answer | assistant / assistant-message | [Yes, on Apple Silicon it should be able to use PyTor...](../exchanges/0453-019e09be-yes-on-apple-silicon-it-should-be-able-to-use-pytorch-s-mps-backend-but-pyan.md) | Yes, on Apple Silicon it should be able to use PyTorch’s mps backend, but pyannote defaults to CPU unless we explicitly move the pipeline/model to that device. I’m stopping the CPU run and checking MPS support before rerunning the sample. |
| 464 | assistant-answer | assistant / assistant-message | [MPS is available and the pyannote pipeline exposes `...](../exchanges/0464-019e09be-mps-is-available-and-the-pyannote-pipeline-exposes-to-so-i-m-going-to-u.md) | MPS is available and the pyannote pipeline exposes .to(...), so I’m going to use pipeline.to(torch.device("mps")). The CPU process didn’t accept an interrupt through this shell session, so I’m locating that one process and stopping it before rerunning on the Apple GPU. |
