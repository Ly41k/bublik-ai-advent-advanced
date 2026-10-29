# Day 7 — Developer Task Router: owner-reported results

On 2026-10-29 Control accepted experiment execution from the owner's local Mac outputs. Work did not
access the private corpus or independently rerun training/evaluation. This is publication staging;
publication and the final private dataset/adapter submission route are still pending.

The task maps a developer request to exactly BUG_FIX, FEATURE, TEST, DOCS, REFACTOR or NEED_INPUT.
Gold correctness and format validity use the entire exact raw response; there is no trim or repair.
Owner-reported accepted data: 200 train / 40 valid; separate sealed 60 eval, 36 EN / 24 RU, 10 per class.
The combined train/validation pool contains 216 new synthetic requests and 24 new fictional requests inspired by public
Bublik Day 6 documentation. Internal 28,680 and cross-split 14,400 lexical comparisons flagged 0 pairs.
The owner reviewed source rights, languages and scenario families, plus a genuinely random 30-item
human audit after frame/seed commitment: 30 PASS, 0 corrections. This is not 240 individual human
approvals, an independent legal audit or a guarantee of complete semantic independence.

Model: mlx-community/SmolLM2-360M-Instruct, revision 5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7.
A supplies user-only task text through the native template, including its default generic system.
B adds one frozen router prompt. C uses the same prompt/eval/greedy decoding and a fresh Day 7 LoRA,
saved then reloaded into a new base instance. Maximum 12 generated tokens. One 150-step run,
batch 4, rank 8, last 8 layers, LR 1e-4; no post-eval prompt selection or retraining.

| Metric | A | B | C |
|---|---:|---:|---:|
| Strict accuracy | 0/60 (0%) | 0/60 (0%) | 40/60 (66.67%) |
| Exact valid label | 0/60 | 0/60 | 60/60 |
| Macro-F1 | 0.0000 | 0.0000 | 0.6242 |
| Wilson 95% accuracy | [0, 6.02]% | [0, 6.02]% | [54.06, 77.27]% |
| Inference total 60, s | 6.937 | 9.963 | 7.013 |
| Median, s | 0.105 | 0.158 | 0.118 |
| Nearest-rank p95, s | 0.134 | 0.180 | 0.139 |

| C class | Correct | Accuracy |
|---|---:|---:|
| BUG_FIX | 2/10 | 20% |
| FEATURE | 5/10 | 50% |
| TEST | 10/10 | 100% |
| DOCS | 10/10 | 100% |
| REFACTOR | 3/10 | 30% |
| NEED_INPUT | 10/10 | 100% |

By language: A/B 0 of 36 EN and 0 of 24 RU; C 26/36 EN (72.22%) and 14/24 RU (58.33%).
Paired B→C: 40 improved, 0 regressed, 0 both correct, 20 both wrong with changed raw output,
0 both wrong with identical raw output. Gain 40/60 = 66.67 percentage points. Exact two-sided McNemar
p = 1.8189894035458565e-12. Since B had no correct cases, zero regressions is a floor effect,
not safety evidence.

Train loss 4.691650390625 → 0.10673856735229492;
validation loss 6.581140041351318 → 0.17431244254112244.
Owner-reported training routine: 77.79578466597013 s (~77.8 s). Source timing includes loading,
training, saving, reloading and checks. Adapter save/reload was TENSOR_IDENTICAL.
Loss is not classification accuracy.

All 60 A and 59/60 B responses reached the frozen LENGTH 12 limit; one B ended at EOS. Neither
baseline produced a strict label. This is a weak prompt baseline, not evidence that alternative
prompting cannot work. C still makes 20 errors; BUG_FIX and REFACTOR are weak. The small balanced
synthetic, owner-curated evaluation does not establish real-traffic or out-of-domain generalization.
The full confusion matrix was not supplied in this aggregate handoff and has not been invented.

Latency excludes model loading and covers generation from tokenized-input readiness to device sync.
Different output lengths limit speed comparisons; a smaller C total in one run is not a speed guarantee.
Monetary/API/electricity costs were not measured. Local-use/derivative rights are owner-attested;
dataset and adapter redistribution is unreviewed. Private eval/gold/per-item outputs/forms/weights
are not included. Final instructor access to private dataset/adapter still requires an approved route.
Historical P9R4 remains SUSPENDED/HOLD; local owner consent is not system-wide native custody proof.

Public staging tests: 100 cases, 88 passed, 12 explicitly skipped (11 corpus-dependent, 1 source-reference
dependent), 0 failures/errors. Code/tests/prompt/policy are byte-identical to R2; only five Markdown
documents were updated. Synthetic smoke is explicitly simulated, not a new ML result. Git/publication
actions and new real model runs have not been performed or authorized by this preparation.
