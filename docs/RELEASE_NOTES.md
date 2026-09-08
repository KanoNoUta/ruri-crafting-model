RURI-Craft G1 (`1.0.0-beta.1`) is the first public crafting model release.

Includes the unchanged FP32 ONNX model, compact PyTorch initialization weights,
feature/action metadata, SHA256 checksums and a ZIP with an offline inference example.
451,404 parameters; 106 features; 36 actions. Code and weights are Apache-2.0.

The README includes four reproducible charts and raw JSON evidence. Historical
teacher-action agreement improves from 84.36% to 92.01% over the prior neural
baseline. A new same-state CPU smoke test shows much lower candidate response
cost than this project's bounded native search; both methods meet the goal in
32/48 sampled continuations. This is not an upstream Raphael benchmark, and no
shorter crafting plans or full-game success guarantee is claimed.

Framework: https://github.com/KanoNoUta/ruri-crafting-framework/tree/v0.1.0

Experimental release; plugin integration is pending. New archived teacher data
has not been merged or used for additional training. Public weights omit the
original optimizer and are intended for inference or custom fine-tuning initialization.
