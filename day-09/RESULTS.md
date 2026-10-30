# Day 9 — Results

Source: the owner's original G6 `PUBLIC_REPORT.md` and `PUBLIC_SUMMARY.json`, reconciled with Control's accepted aggregate results. [RESULTS.json](RESULTS.json) is a byte-identical copy of that supplied public summary. Publication preparation checks consistency; it does not rerun the models or privately replay captures.

## Quality and request latency

All arms have 32 captured attempts on the same original frozen final set and independent gold. Capture completeness 32/32 is separate from accuracy. All four classes have eight cases.

| Arm | Correct | Strict errors | Accuracy | Macro-F1 (0–1) | Median, ms | p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Student Base | 2/32 | 30/32 | 6.25% | 0.076923 | 217.954 | 487.295 |
| Student Tuned | 26/32 | 6/32 | 81.25% | 0.807639 | 97.074 | 110.426 |
| Teacher GPT-OSS 120B / Groq | 30/32 | 2/32 | 93.75% | 0.934874 | 459.115 | 658.353 |

Latency is rounded to three decimal milliseconds, Macro-F1 to six decimals; full values are in JSON. Macro-F1 is the unweighted mean over four labels, with invalid outputs contributing false negatives. p95 is nearest-rank over all 32 attempts, including errors; it is not a production tail-latency guarantee.

Tuned−Base: **+24/32 correct / +75 percentage points**. Tuned−Teacher: **−4/32 correct / −12.5 percentage points**.

Per-request wall time includes local rendering/tokenization/decoding or HTTP/provider processing. Deliberate pacing, model loading and training are excluded. The first query includes cold-kernel effects; there are no hidden warmups. Separate recorded model loading is approximately **0.179637s Base /0.166829s Tuned**. Accepted training time is **74.8423s**, not inference latency. One sample per case, output-length differences and different hardware/API infrastructure limit speed conclusions. No tokens-per-second or throughput comparison is inferred.

## Class errors and format

| Independent gold class | Base errors /8 | Tuned errors /8 | Teacher errors /8 |
|---|---:|---:|---:|
| BUG | 8 | 0 | 0 |
| FEATURE | 6 | 2 | 0 |
| DOCS | 8 | 1 | 0 |
| NEED_INFO | 8 | 3 | 2 |
| Total errors /32 | 30 | 6 | 2 |
| Invalid outputs (subset of errors) | 27 | 0 | 0 |

Invalid is included in the class error totals, not an extra error category to add to them. Base has 27 invalid outputs and three incorrect valid labels. Tuned produces valid class labels for all 32 cases but misclassifies six. Its main remaining difficulty is NEED_INFO: three errors, spread across BUG, DOCS and FEATURE; both Teacher errors are also NEED_INFO. Tuned's FEATURE errors both predict NEED_INFO, and its DOCS error predicts BUG. Full confusion matrices are retained in JSON.

## Paired Teacher / Tuned coverage

| Outcome on the same 32 cases | Count |
|---|---:|
| Both correct | 24 |
| Only Teacher correct | 6 |
| Only Tuned correct | 2 |
| Both wrong | 0 |

This supports 26 observed Tuned successes, while six cases still favour Teacher. The two Tuned-only successes show Teacher can also be wrong. No confidence detector or routing rule capable of identifying those cases was benchmarked.

## Safe anonymous examples

These are the seven examples already selected in the supplied public report. Only alias, gold class and predicted labels are shown; no original ID, family, question or raw response is published.

| Alias | Gold class | Base | Tuned | Teacher | Tuned correct |
|---|---|---|---|---|---|
| E01 | BUG | INVALID | BUG | BUG | Yes |
| E02 | FEATURE | INVALID | FEATURE | FEATURE | Yes |
| E03 | FEATURE | FEATURE | NEED_INFO | FEATURE | No |
| E04 | DOCS | INVALID | DOCS | DOCS | Yes |
| E05 | DOCS | INVALID | BUG | DOCS | No |
| E06 | NEED_INFO | INVALID | NEED_INFO | NEED_INFO | Yes |
| E07 | NEED_INFO | INVALID | BUG | NEED_INFO | No |

E03 illustrates a Base-correct FEATURE becoming wrong after tuning. E05/E07 show valid output format with the wrong label. E01/E02/E04/E06 illustrate Tuned successes where Base output was invalid. These examples do not expose the original scenario or establish new semantic properties of a class.

## Nominal API cost and savings

| Arm | API USD /32 | API USD /query |
|---|---:|---:|
| Student Base | 0 | 0 |
| Student Tuned | 0 | 0 |
| Teacher | 0.00180975 nominal | 0.0000565546875 nominal |

Using local inference instead of 32 teacher calls avoids **$0.00180975 nominal API fee**, or **$0.0000565546875/query**. This is the source report's list-price calculation, not proof of a monetary saving on Groq Free.

The evaluation records **PRICING_VERIFIED**, source [Groq GPT-OSS120B documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b), tariff as_of **2026-10-30**, verified_at **2026-10-30T21:09:23+00:00**. USD per 1M tokens: **input $0.15 / cached input $0.075 / output $0.60**. This is the saved evaluation tariff; publication preparation performs no new rate lookup and makes no claim about a later tariff.

The original G6 calculation uses returned usage: uncached input ×input rate +cached input ×cached rate +output ×output rate, divided by1M. Reasoning is already part of output. Cache breakdown is absent for all 32 records, so cached input is conservatively treated as0. The aggregate public files do not expose token totals; this stage checks the recorded fee and per-query arithmetic, not an independent reconstruction from private API usage.

Actual billed amount/Free billing is **NOT_OBSERVED**. Local API fee is $0; hardware, electricity and amortization are **NOT_MEASURED**. Labeling/pilot setup, training and model loading do not enter per-query API savings. Total monetary ROI and break-even were not measured.

## Conclusion and historical limits

The single LoRA run makes this small classifier much more useful on the frozen task, particularly for output format and BUG classification. FEATURE, DOCS and NEED_INFO errors remain, with NEED_INFO the weakest class. The student can support a narrow workflow with review where errors matter; unconditional replacement is not established by 32 cases. Suggested review/routing remains a recommendation, not a measured deployment system.

`PILOT_PASS=STOP` is preserved. No final result is used for new training, checkpoint selection, altered gold or a relaxed scoring rule. Course Minimum acceptance and this publication report do not rewrite that history.
