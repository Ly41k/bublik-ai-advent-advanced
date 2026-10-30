# Day 9 — Reproducibility

This is a report-only publication package. It contains no runnable training/inference pipeline, private dataset, gold, prompt, raw model answer, provider context, capture, audit decision or weights. The original public G6 report/summary are supplied and reconciled. No empirical replay is claimed by this static preparation. RESULTS.json preserves the supplied public summary byte for byte.

## Model and training configuration

The existing accepted Day 9 launcher/configuration records:

| Setting | Value |
|---|---|
| Student snapshot | `mlx-community/SmolLM2-360M-Instruct` |
| Revision | `5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7` |
| Teacher | `openai/gpt-oss-120b` through Groq |
| Method | One LoRA run; rank 8, scale 20, dropout 0 |
| Targets | q/v attention projections, last 8 layers |
| Optimizer updates | 150 |
| Batch / accumulation | 4 /1 |
| Learning rate | 0.0001 |
| Training seed | 20261029 |
| Prompt loss | Masked |
| Maximum training sequence | 512 tokens |
| Validation | All 16 records; every 25 updates |
| Checkpoint candidates | 50,100,150 |
| Selection | Lowest full validation loss; tie uses earliest |
| Selected checkpoint | 150 |
| Accepted training runtime | 74.8423 seconds |
| Environment | Python 3.13.3; mlx 0.32.4; mlx-lm 0.32.2; transformers 5.21.0; huggingface_hub 1.33.0 |

The Day 9 launcher retains the original Day 9 chat messages and uses existing checked Day 8 components. The tokenizer compatibility fix preserves local-only loading and `trust_remote_code=False`. Day 8 source components are unchanged. This publication stage runs no ML and changes no hyperparameters.

## Frozen split and isolation

The approved protocol has 12 separate pilot cases, 100 original candidates and 32 independent final cases. Teacher answers are filtered against independent gold; eight disagreements stay rejected. Mandatory owner review concludes before the eligible 92 supply the deterministic 64/16 split. Twelve eligible reserve records remain outside training/validation. Supplemental questions are excluded.

| Class | Train | Valid | Frozen final |
|---|---:|---:|---:|
| BUG | 16 | 4 | 8 |
| DOCS | 17 | 4 | 8 |
| FEATURE | 17 | 4 | 8 |
| NEED_INFO | 14 | 4 | 8 |
| Total | 64 | 16 | 32 |

Control explicitly approved these unequal train quotas. The earlier 20-per-class requirement was revised before training; rejected teacher answers were not recovered to fill quotas. Independent gold, teacher agreement and prior owner decisions are retained.

The private pipeline verifies source freezes, deterministic IDs, exact/normalized text separation, family separation and static semantic scenario review across pilot/train/valid/final. A pilot-related DOCS overlap was resolved with an independent reserve before training. This is scenario review plus deterministic checks, not a mathematical proof of semantic independence. Final outcomes are not used to select training items, the checkpoint or another training run.

## Final evaluation contract

Base and Tuned share the pinned model/tokenizer/chat template, frozen system/user messages, greedy temperature 0, seed 9001 per request, max 64 new tokens, no stop strings or hidden warmups and a fresh stream per case. The historical initial student limit 8 is not rewritten; pilot recovery and final student evaluation use 64.

Teacher uses the same semantic task and frozen messages with native Groq serialization: temperature 0, top_p 1, low reasoning effort, max_completion_tokens 256 including reasoning, n 1, nonstreaming. Provider-native serialization differs from local MLX. Each arm has one attempt per frozen ID; no hidden retries. Errors/truncation/extra whitespace/text/tools fail strict scoring.

Recorded latency excludes deliberate pacing and model loading; training time is separate. Teacher cost uses actual captured prompt/completion/cached usage at the recorded nominal tariff when sufficiently verified, reasoning counted once as output. Local API cost 0 excludes local resources. The supplied G6 public outputs record PRICING_VERIFIED for the saved 2026-10-30 tariff. Publication preparation retains that historical status and performs no new price lookup. Actual Free billing remains NOT_OBSERVED; source fee arithmetic is checked without access to private token-level usage.

## Reproduction order and limits

1. Read RESULTS.json and recompute correct/accuracy, four-class macro-F1, error totals and paired counts from its aggregate confusion matrices. Cross-check the rounded Markdown tables and accepted Control figures. Median/p95 values are copied from the saved report; reproducing those statistics from individual timings requires private evidence.
2. With the owner's retained private artifacts, verify source/capture freezes and every file SHA, original final32 gold/messages/settings/request hashes, split/audit lineage and checkpoint150 provenance.
3. Run the existing offline report compatibility launcher over saved captures only. It does not repeat live admission, API calls, inference or training.
4. Reconcile its saved public report/summary with these documents: accuracy, macro-F1, class errors, timings, nominal cost, pricing status and safe anonymous examples. The supplied summary is retained unchanged as RESULTS.json. Both source hashes are recorded below; model calls are unnecessary for this offline reconciliation.
5. Review privacy and the exact public file allowlist; retain raw evidence separately.

The public package alone cannot reproduce model outputs, inspect independent per-item gold, train/reload the adapter, or independently prove the private isolation checks. New experiments are not part of publication preparation. Source reconciliation is complete. This final staging requires independent Control Review and separate authorization before any GitHub write. `PILOT_PASS=STOP` remains historical fact.

## Public source identity

SHA256 of the supplied original public files:

- PUBLIC_REPORT.md: `81685903437072a54dcd91f8abf2002e42ff0f1638c9b2532adff8cd097e5221`.
- PUBLIC_SUMMARY.json, identical to RESULTS.json: `c5116aea094ab014618b0baea7609abdbdfda31eac791c23909dda77f2c91a13`.

Only four files are in the public staging: README.md, RESULTS.md, REPRODUCIBILITY.md and RESULTS.json. Preparation evidence, source archive metadata, tests and GitHub preflight remain outside that public allowlist. No private source path or raw example is needed to check these aggregates. Per-item isolation, model execution and usage provenance remain based on the accepted private Mac evidence.
