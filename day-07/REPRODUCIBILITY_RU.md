# Воспроизводимость: source, synthetic checks и owner report

Публичное дерево содержит ровно 19 путей из allowlist R2 release:
`59c91f606163627146d2db61c9523c27001bcc9db43ca6d673ab603c9ade3319`.
Source ZIP CRC и исходный manifest 69/69 проверены. 14 code/test/prompt/policy файлов оставлены
побайтово; изменены только README_RU.md, SUMMARY_EN.md, REQUIREMENTS_MATRIX.md,
PUBLICATION_ALLOWLIST_RU.md и этот файл. Не импортируются Day 6 checkpoints или прежние R3 implementations.

Source-defined protocol: SmolLM2-360M-Instruct revision 5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7,
MLX LoRA, rank 8 / scale 20 / dropout 0, q/v последних 8 слоёв, Adam LR 1e-4, batch 4,
150 iterations, max training length 512, mask_prompt, full valid 40; greedy max 12 new tokens.
Source целится в Mac arm64/Python 3.13.3/UCD 15.1.0, mlx 0.32.4/mlx-lm 0.32.2,
transformers 5.21.0/huggingface_hub 1.33.0. Здесь это source pins, не новая независимая проверка
фактического owner hardware/stack. Control сообщил local snapshot/tokenizer/masking PASS.

Текущие реальные агрегаты основаны исключительно на owner Mac outputs, принятых Control 29.10.2026.
Work не получал eval/gold/accepted dataset/adapter/частные runtime receipts и не повторял ML-run.
Не изменялись prompt, decoding, scorer, training config или выводы. Source offline status strings
остаются историческими; их нельзя использовать для отмены последующих owner-reported результатов.

Из day-07 можно повторить только публичные безопасные проверки:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B run.py synthetic-smoke
```

Фактический staging результат: 100 cases, 88 passed, 12 SKIP, 0 failures/errors.
12 Python source files проверены ast.parse без model imports/bytecode. 11 unit cases зависят от
непубликуемого candidate corpus; 1 — от original generator reference. Их skip причины:
PRIVATE_CORPUS_NOT_PUBLISHED / PUBLIC_REFERENCE_NOT_PUBLISHED; это не PASS по данным или codec.
В полном R2 source package ранее были 100/100, но здесь публикуется другой subset и его честные counts.
Synthetic smoke использует искусственные records, human/permission/ML test doubles, не настоящие
approvals или model inference. Симулированные числа smoke не смешиваются с owner A/B/C.

CLI check/admission/freeze/audit/train/eval требуют полного reviewed owner package и private inputs;
они не становятся runnable end-to-end из этого public subset. Реальный новый запуск требует отдельного
owner/Control решения. Скачивание весов, auto retry/resume или новые experiments не разрешены.

Публичные результаты — округлённые aggregates, а не raw predictions или доказательство независимой
семантической проверки. Macro-F1, latency и losses приняты из handoff; Work проверил только внутреннюю
арифметическую согласованность counts/denominators. Missing full confusion matrix не реконструировалась.
Source timer training routine включает load/train/save/reload/checks, latency excludes model load.
Одно наблюдение времени не гарантирует ускорение или экономию. Денежные/энергетические затраты не измерены.

Локальные права на два train sources и eval generation lineage OWNER-ATTESTED; redistribution не
разрешён. Dataset/adapter остаются у владельца. Для зачётной передачи приватных артефактов нужен
согласованный способ доступа преподавателя; Work не просит выгружать их в чат/GitHub.
P9R4 historical native/custody HOLD остаётся, owner-local consent не является system-wide no-sync proof.
