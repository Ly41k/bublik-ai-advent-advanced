# Day 9 — Teacher-to-student distillation (Бублик)

**Course Minimum: ACCEPTED by Control from Mac evidence.** Final publication staging; GitHub publication requires a separate Control decision. Results are reconciled with the supplied original G6 `PUBLIC_REPORT.md` and `PUBLIC_SUMMARY.json`. No new model runs were performed during publication preparation.

## Task and models

Classify a technical request as exactly one label:

| Label | Meaning |
|---|---|
| BUG | A defect in existing behaviour |
| FEATURE | A requested new capability |
| DOCS | Documentation or explanation work |
| NEED_INFO | Insufficient information to classify or act |

The teacher is **GPT-OSS 120B through Groq**, model `openai/gpt-oss-120b`. The student is local **SmolLM2-360M-Instruct**, compared before and after one LoRA run. Teacher answers are checked against independent gold before training.

## Method

The protocol separates 12 pilot cases, 100 frozen training candidates and the original 32 frozen final cases. Eight candidate teacher answers disagree with independent gold and stay rejected. After owner audit, 92 candidates are eligible; a deterministic 64 train /16 valid split uses approved unequal training quotas. Twelve eligible records remain in reserve; no supplemental batch is used.

Gold and messages are unchanged. Isolation checks cover pilot, train, validation and final test. Strict scoring accepts only the exact raw class label with `stop`, no tools and no error. Truncation, explanations, extra whitespace and malformed output count as errors. There are no score-improving retries or test-based checkpoint changes.

One local LoRA run completed **150/150 updates**, with **best checkpoint 150** and **training runtime 74.8423 seconds**. Historical **`PILOT_PASS=STOP` remains unchanged**; the later final comparison and Course Minimum acceptance are separate outcomes.

## Final comparison

| Model | Correct /32 | Accuracy | Macro-F1 (0–1) | Median latency | API USD /32 |
|---|---:|---:|---:|---:|---:|
| Student Base | 2/32 | 6.25% | 0.076923 | 218 ms | 0 |
| Student Tuned | 26/32 | 81.25% | 0.807639 | 97 ms | 0 |
| Teacher GPT-OSS 120B | 30/32 | 93.75% | 0.934874 | 459 ms | 0.00180975 nominal |

Median values here are rounded to whole milliseconds; Macro-F1 is rounded to six decimals. [RESULTS.json](RESULTS.json) retains the original public summary without numeric changes.

Tuned gains **24 correct answers / +75 percentage points** over Base. It remains **4 correct answers /12.5 percentage points** below Teacher on this set. Base has 27 invalid outputs; Tuned has none, with six remaining class-label errors. The observed tuned median is lower on this Mac; output lengths, cold-kernel effects and local/provider infrastructure limit interpretation of speed.

At the recorded nominal tariff, replacing 32 teacher calls with local calls avoids **$0.00180975 nominal API fee**. Local API fees are $0. Groq Free actual billing is **NOT_OBSERVED**; equipment, electricity, depreciation, labeling setup and training are outside this per-query comparison.

[Detailed results, class errors and anonymous examples](RESULTS.md) · [Protocol and reproduction limits](REPRODUCIBILITY.md).

## Applicability and limits

Tuned is correct on all eight BUG probes, seven DOCS, six FEATURE and five NEED_INFO probes. It can help with this narrow, low-risk classification task where errors can be reviewed. Six remaining failures prevent a claim of unconditional teacher replacement. Teacher is also imperfect; the two Teacher-wrong cases are Tuned-correct in the paired comparison.

These are 32 closed cases, eight per class, one training run and one seed. Confidence routing, production reliability, local resource cost and monetary break-even were not measured. Private data, gold, prompts, raw answers, audits, provider contexts, captures and weights are not distributed. No private question is reconstructed from an anonymous example.
