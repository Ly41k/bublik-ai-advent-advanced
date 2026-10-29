# Reproducibility and publication checks

This is a report-only publication package. It contains the sanitized English report,
aggregate measurements, the supplied loss chart and static verification code/tests.
It does not contain datasets, reference answers, individual generated outputs, model
weights, a training/inference runner, approvals or private execution evidence.

## What can be checked here

From this `day-08/` directory, Python 3.10+ standard library only:

```sh
python3 -B verify_publication.py
python3 -B -m unittest discover -s tests -v
```

The first command checks the exact file allowlist, SHA256 manifest, chart identity,
PNG CRC, aggregate arithmetic and required limitations. Tests also reject altered
metrics and missing caveats. These checks do not load a model, execute training or
inference, contact GitHub, or publish anything. PASS means static consistency of this
package; it does not mean the model was rerun or the empirical measurements independently
reproduced from public data. The chart is the original supplied PNG, unchanged.

## Experiment protocol

SmolLM2-360M-Instruct revision `5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7`;
one fresh LoRA, rank 8 / scale 20, q/v projections in the last 8 layers, batch 4,
learning rate 1e-4, 150 optimizer updates; 96 train and 20 full-validation items.
Greedy generation, temperature 0, maximum 96 new tokens. The primary evaluation
was fixed before the model runs: FORMAT 8 / STYLE 8 / KNOWLEDGE 12 / OOD 12.
The 12 knowledge questions probe six fictional facts directly and by paraphrase;
the same facts intentionally occur in training. This is not a disjoint-facts holdout.

Base has no specialty system instructions; Base+Prompt and Tuned share the frozen
specialty prompt for in-domain tasks. OOD uses the same neutral task prompting for
Base and Tuned. Base+Facts supplies the six facts as context on knowledge questions
only: its denominator is 12, and it is not an actual RAG system or retrieval benchmark.
No prompts or item-level material are distributed in this package.

Official full validation uses post-update states at 25/50/75/100/125/150. The train
loss series is the mean of the preceding 25 mini-batch losses, each computed before
its own optimizer update; it is not full-train loss on the post-update weights.
Separate checkpoints were saved at 50/100/150, with Best selected strictly by full
validation loss among those three (tie: earliest), never by primary evaluation.
Best=Late=150, so this run does not compare distinct best and late weights.

The frozen overfit signal requires two consecutive validation-loss increases while
train loss decreases. It was NOT_OBSERVED. This does not remove the observed OOD
regressions. There was no reserve evaluation or retraining.

## Limits of public reproduction

The results are accepted aggregates from the independent G4 Control Review. That
review recomputed the frozen scores from private outputs and the frozen scorer;
publication preparation did not repeat ML or modify the benchmark. Private material
is retained separately and is outside this public allowlist. This package alone cannot
reproduce model answers, verify per-item gold, train the adapter or independently
confirm native tensor reload. No public model availability is implied.

Post-hoc OOD content review (Base 9/12, Tuned 3/12) is manual Control adjudication,
separate from strict OOD (1/12, 2/12). Owner adjudication of the strict regression is
still PENDING; owner approval is not claimed. Twelve OOD probes cannot establish
broad model-wide degradation. Exact factual recall is only 1/12 probes (1/6 direct,
0/6 paraphrase), despite the overall 11/40 strict score.

Generation timing excludes model loading/tokenization and compares different output
lengths. Training time includes loads, validation/checkpoints and reload. Disk bytes
are not RAM use. Money, electricity, peak RAM and monetary savings were NOT_MEASURED;
no end-to-end speedup, monetary ROI or RAG advantage is established.

This staging remains unpublished and requires separate Control publication approval.
