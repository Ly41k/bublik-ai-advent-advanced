# Day 10 — Results

**Course Minimum: ACCEPTED by Control from the retained Mac evidence.** The one accepted local run is reported below. Publication preparation only rechecks saved evidence and source identity; it performs no native model execution.

## Quality and HTTP latency

| Model | Correct /32 | Accuracy | Macro-F1 | Invalid | HTTP median, ms | HTTP p95, ms | Load, s | Logical model, MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BASE | 2/32 | 6.25% | 0.076923 | 27 | 226.439 | 488.973 | 1.026375 | 694.75 |
| Q4 | 20/32 | 62.50% | 0.605006 | 0 | 91.685 | 94.199 | 0.214071 | 197.67 |
| FP16 | 27/32 | 84.38% | 0.838294 | 0 | 96.341 | 107.195 | 0.203425 | 693.53 |

**Selected: fused FP16.** The single affine4/group64 candidate reached20/32, below the predeclared24/32 threshold. Its quantization/export succeeded technically, but its quality criterion failed. The already prepared FP16 fallback reached27/32. No second quantization candidate, training run or parameter search followed.

FP16 improves over Base by25 correct answers /78.125 percentage points; Q4 loses7 correct answers relative to FP16. Day9 tuned+adapter scored26/32; fused FP16 scores27/32 here. That one-case difference is an observed packaging/runtime comparison, not evidence of new training or a general improvement.

Load includes materialization/synchronize and excludes byte validation and readiness smoke. Base was the startup load; Q4/FP16 were later switches, so cache/order differences prevent treating load times as repeated cold-start comparisons. Fusion took1.031842s, quantization0.496543s; full recorded preparation18.495504s.

## Process and MLX memory

| Model | Sampled RSS max, MiB | Process lifetime RSS high-water at this arm, MiB | MLX active max, MiB | MLX cache max, MiB | MLX lifetime peak observed at this arm, MiB |
|---|---:|---:|---:|---:|---:|
| BASE | 881.66 | 885.05 | 691.12 | 38.57 | 977.53 |
| Q4 | 438.28 | 1151.02 | 197.17 | 15.77 | 1137.94 |
| FP16 | 957.42 | 1180.11 | 691.12 | 11.07 | 1153.18 |

RSS samples are not exact instantaneous peaks. Process high-water and MLX peak are cumulative for one service lifetime and include overlap during switches; they are not isolated model-only memory. Active and cache maxima are reported separately and need not occur at the same instant. MiB=2^20bytes.

During final FP16→Base rollback, the recorded sample with both models after smoke was1681.06MiB RSS; process high-water reached1682.98MiB and MLX lifetime peak1646.86MiB. This temporary overlap explains why lifetime peaks exceed steady per-arm samples.

Allocated disk bytes for Base/Q4/FP16:728518656 /207294464 /727244800. Logical bytes:728493041 /207272453 /727219998. Filesystem allocation may share APFS blocks; sizes include model-directory metadata/tokenizer files.

## Switching, failure handling and rollback

- Base→Q4→FP16 hot switches completed in one service process; all scored responses matched its PID/instance and frozen prompt-serialization hashes.
- Loading the fixed missing-weights candidate produced the expected loader FileNotFoundError /HTTP503. The working FP16 version and its diagnostic prediction were preserved; failure request wall time2.803ms.
- FP16→Base rollback passed with unchanged PID/instance and working /classify. Base load0.170793s; whole rollback HTTP request684.762ms, including validation/readiness/release. Actual process identifiers remain private.
- Paired Base/selected FP16: both correct1, Base-only1, FP16-only26, both wrong4. This reconciles2 Base successes and27 FP16 successes.
- Day9 verification passed before/after. Training, external model API calls and Git writes in this run were0. The final active model was Base.

## Versions and provenance

Python3.13.3; mlx0.32.4; mlx-lm0.32.2; transformers5.21.0; huggingface_hub1.33.0. FastAPI0.121.0; Uvicorn0.38.0; Pydantic2.14.2. Student: mlx-community/SmolLM2-360M-Instruct, revision5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7; Day9 checkpoint150.

Accepted private registry SHA256: `13ee46f7df01a86312cf4fec92eb9a18d61ae5862d6df661f476873994342689`.

Model versions: `base-155787fb371d6ec4`, `q4-d788a4a486f4ab61`, `fp16-3193e5589dc4dd44`.

The saved Control JSON, its SHA manifest and the original renderer-reconstructed REPORT agree. REPORT reconstruction uses the original arm order; its4342 bytes and SHA256 match the retained evidence manifest exactly. Raw requests/responses and per-item gold were not supplied or replayed for publication; no independent per-item latency reconstruction is claimed.

Public code has the path/bookkeeping adaptation documented in README. Service bytes match the measured source; fusion/inference/scoring/selection/rollback algorithms are preserved by static comparison. The adapted public wrappers have not been rerun with real models; the metrics belong to the original measured implementation, not a claimed new public-code run.

## Measurement limits

This is one sequential run on the known frozen32-case deployment regression set, eight cases per class. FP16 is a useful fallback on this set; five classification errors remain. It does not establish reliability on unseen production traffic. The run has explicit one-token technical readiness forwards on loads and four separate diagnostic classifications, all excluded from final32 scoring. No score-improving retries occurred.

HTTP timing includes localhost serialization, inference and memory sampling. Server-generation median/p95 (ms) were: Base216.103/478.693, Q4 82.597/85.367, FP16 86.899/96.936. p95 uses nearest rank of32 attempts; it is not a production tail-latency guarantee. First requests retain remaining cold-kernel effects. Base/Q4 differ in weight precision and output lengths, so speed/memory differences cannot be assigned solely to tuning.

See README for immutable-directory verification, switching and rollback. Private models, datasets, prompts, captures, registry contents and actual PID/instance IDs are not published.
