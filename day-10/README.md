# Day 10 — Local tuned-model service (Бублик)

**Course Minimum: ACCEPTED by Control from the retained Mac evidence.**
SmolLM2-360M-Instruct checkpoint150 from Day9 is fused into a local MLX model
and served through FastAPI. Base/Tuned switching and rollback keep the same
process. The sole 4-bit candidate scored20/32, below the predeclared24/32
threshold; fused FP16 scored27/32 and was selected.

See [RESULTS.md](RESULTS.md) for measured quality, latency, load time and memory.
This publication preparation performs no training, inference or model API calls.

## Files and prerequisites

- `prepare_model.py`: native LoRA fusion → FP16, one affine4/group64 conversion.
- `service.py`: GET `/health`, POST `/classify`, POST `/model`.
- `benchmark.py`: Base32 → Q4 32, FP16 32 only after Q4 quality failure;
  failed-load preservation and rollback.

Pinned runtime: Apple Silicon macOS, Python3.13.3, mlx0.32.4, mlx-lm0.32.2,
transformers5.21.0, huggingface_hub1.33.0. Service dependencies used in the
accepted run: FastAPI0.121.0, Uvicorn0.38.0, Pydantic2.14.2.

The owner-retained Day9 G5/Recovery/tokenizer verifier, its supporting source
overlays, frozen final32/gold, audit/split/training provenance, checkpoint150 and
the pinned local Base snapshot are required. They are **not distributed here**.
Day9 in this repository is report-only; a public checkout alone cannot reproduce
the measured model outputs. This package exposes the implementation and explicit
input contract; private prerequisites retain their original identity and checks.

## Public path adaptation

The measured implementation is retained unchanged privately. This public copy
replaces its machine-specific directory defaults with an explicit private JSON
configuration. Fusion, quantization, generation, scoring,24/32 selection,
locking, candidate-load commit and rollback algorithms are unchanged.
`service.py` is byte-identical to the measured source. `benchmark.py` changes
only two calls that read the new path mapping. Preparation changes are confined
to path binding, CLI/configuration and source-identity bookkeeping.

The original probe is omitted: it is not imported or executed by the runtime.
Its only production reference was a source-manifest entry; the public manifest
now binds the three runtime scripts and this README. Existing private registries
are intentionally rejected by the changed source hashes: do not rewrite them or
overwrite the accepted Day10 output. A public-copy rerun needs a fresh output;
no rerun is claimed or required for publication review.

## Configure private inputs

Create a JSON file outside the repository; replace every placeholder with the
actual absolute path. These are the13 required keys, matching the existing
Day9 verifier arguments. No dataset, prompt or secret belongs in this config.
The referenced inputs must already pass the accepted Day9 checks, including
their required permissions and lineage; changing a path does not relax them.

```json
{
  "g5_path": "/absolute/private-inputs/g5-final32-r1/g5.py",
  "recovery_source": "/absolute/private-inputs/g3-recovery-r1",
  "tokenizer_source": "/absolute/private-inputs/tokenizer-compat-fix-r1/train_day9.py",
  "source": "/absolute/private-inputs/day9-frozen-source",
  "g2_source": "/absolute/private-inputs/labeling-source",
  "r70_source": "/absolute/private-inputs/remainder-source",
  "diagnostic_source": "/absolute/private-inputs/diagnostic-source",
  "owner_source": "/absolute/private-inputs/audit-source",
  "derived": "/absolute/private-inputs/derived.json",
  "audit": "/absolute/private-inputs/audit.json",
  "split": "/absolute/private-inputs/accepted-split",
  "training": "/absolute/private-inputs/accepted-training",
  "model": "/absolute/local-models/pinned-base-snapshot"
}
```

## Prepare and start

From repository root, set the pinned interpreter and explicit input/output paths.
The output parent must exist; the output itself must not exist. Model operations
use local paths, offline HF settings and an outbound IP/DNS guard.

```bash
D10_PYTHON=/absolute/pinned-environment/bin/python
D10_PATHS=/absolute/private-inputs/day9-paths.json
D10_OUTPUT=/absolute/private-output/day10-new-version

"$D10_PYTHON" -B day-10/prepare_model.py \
  --paths "$D10_PATHS" --root "$D10_OUTPUT" --install-service-deps
```

The optional install flag adds FastAPI/Uvicorn and missing dependencies under
constraints pinning every existing distribution. It does not allow upgrades to
the MLX/transformers stack. Installation alone contacts the package index;
model operations contact no model API or model hub. Resolver conflict means STOP.
If dependencies already exist, omit the flag.

Preparation verifies the original G5/checkpoint150/source lineage, saves fused
FP16 and one affine4/group64 candidate, then writes private model inventories
and `REGISTRY.json`/`REGISTRY.sha256`. It does not measure quality. Separate fixed
missing-weights fixture data exercise real loader failure; they are not another
quantization candidate.

In another terminal, set the same interpreter and output variables, then:

```bash
"$D10_PYTHON" -B day-10/service.py --root "$D10_OUTPUT" --enable-load-failure-test
```

The service listens only on `127.0.0.1:8010`, one worker, no reload or docs routes.
Initial model is Base. One lock and one event-loop thread serialize MLX calls.
Candidate weights are hash-checked, loaded/materialized and passed through an
explicit one-token technical readiness forward before swapping the active
reference. Until commit, the previous model object remains available; during
loading requests wait and both models can occupy memory. Loader exceptions keep
the working reference; an OS-level process kill is outside this guarantee.
The test flag only enables the fixed missing-weights fixture, not arbitrary
model paths. Omit it for later ordinary service use.

## Benchmark, release and rollback

Only with authorized retained private inputs, one new benchmark invocation:

```bash
"$D10_PYTHON" -B day-10/benchmark.py --root "$D10_OUTPUT"
```

It evaluates identical frozen messages through HTTP: greedy temp0, seed9001 per
request, max64, context2048 and fresh KV cache. Raw labels are scored exactly;
whitespace, extra text and length termination fail. There are no retries or
quantization parameter searches. Q4 <24/32 selects the already prepared FP16
fallback, which must also pass24/32. Readiness forwards and four diagnostic
classifications of a separate technical string are excluded from final32.

The run saves the accepted variant in private `SELECTION.json`, validates real
failed-load preservation, then rolls back to Base and verifies unchanged PID,
instance and working classification. Existing benchmark output is never reused.
Generated reports/captures stay outside the repository and require privacy
review before any sharing.

After a successful benchmark, enable the selected Tuned without restart:

```bash
curl --noproxy '*' -sS http://127.0.0.1:8010/model \
  -H 'Content-Type: application/json' -d '{"model":"tuned"}'
curl --noproxy '*' -sS http://127.0.0.1:8010/health
curl --noproxy '*' -sS http://127.0.0.1:8010/classify \
  -H 'Content-Type: application/json' -d '{"text":"Add an export button."}'
```

Rollback, checking `active=base` and unchanged process identity:

```bash
curl --noproxy '*' -sS http://127.0.0.1:8010/model \
  -H 'Content-Type: application/json' -d '{"model":"base"}'
curl --noproxy '*' -sS http://127.0.0.1:8010/health
```

Release storage uses immutable model directories/version IDs and recorded SHA
inventories. Preserve the working Base and prior artifacts for rollback. New
releases need a new registry/output, hash verification, offline load/readiness
and explicit quality verification before selection. This minimal service has a
fixed registry; registering arbitrary future versions while it runs is not
implemented. Base/Tuned selection within that registry requires no restart.

Weights, adapters, private input mappings, prompts, datasets/gold and raw
captures are excluded from this public package. Publishing code does not grant
redistribution rights over those retained private artifacts.
