# Бублик — Day 7: Developer Task Router

Компактная локальная модель маршрутизирует запрос разработчика в одну из шести точных меток:
`BUG_FIX`, `FEATURE`, `TEST`, `DOCS`, `REFACTOR`, `NEED_INPUT`. Верный ответ — весь raw-ответ,
буквально равный gold. Scorer не исправляет пробелы, объяснения, регистр или перенос строки.
`NEED_INPUT` означает отсутствие определимого поддерживаемого результата, а не просто нехватку кода.

**Состояние на 29.10.2026:** Control принял выполнение эксперимента по owner-reported выводам
локального Mac. Work при подготовке публикации не читал приватные данные и не повторял ML-запуски.
Публичная сборка ожидает Control Review; публикация не выполнена. Доступность приватных dataset
и adapter преподавателю требует отдельного способа передачи и разрешения.

## Данные и протокол

- Владелец сообщил admission 200 train + 40 valid и отдельный frozen eval 60: 36 EN / 24 RU,
  по 10 на класс. В 240 train/valid — 40 записей на класс, 144 EN / 96 RU.
- 216 новых synthetic запросов и 24 новых fictional fact-inspired запроса по публичной документации
  Бублика Day 6. Это не реальные чаты/тикеты. Local-use/derivative права — OWNER-ATTESTED,
  не независимый юридический аудит; redistribution корпуса и адаптера не разрешён.
- Машинные проверки: 28 680 внутренних и 14 400 cross-split пар, 0 flags. Владелец подтвердил
  language/family/global scenario review; разные IDs и отсутствие lexical flags не доказывают
  semantic independence. Исторический review 60 gold — OWNER-ATTESTED.
- После фиксации frame CSPRNG seed сохранён до draw. Реальный owner audit 30: 30 PASS, 0 corrections.
  Это не 240 индивидуальных human approvals.

Модель: `mlx-community/SmolLM2-360M-Instruct`, revision
`5d5e6fee5beb5d4d4d85e2203ef23e1230a9aac7`, локальный MLX.
A — base с user-only task text через native chat template, который добавляет **generic system**.
B — та же base с единственным frozen router prompt. C — новый Day 7 LoRA с тем же prompt/eval/decoding,
что B, после сохранения и tensor-identical reload. Greedy, максимум 12 новых токенов, новый request cache.
Один run: 150 iterations, batch 4, rank 8, последние 8 слоёв, LR 1e-4. Подбора по eval не было.

## Owner-reported результаты

| Метрика | A | B | C |
|---|---:|---:|---:|
| Strict correct / accuracy | 0/60 (0%) | 0/60 (0%) | 40/60 (66.67%) |
| Exact label format | 0/60 | 0/60 | 60/60 |
| Macro-F1 | 0.0000 | 0.0000 | 0.6242 |
| Wilson 95% accuracy | [0, 6.02]% | [0, 6.02]% | [54.06, 77.27]% |
| Сумма latency 60, seconds | 6.937 | 9.963 | 7.013 |
| Median, seconds | 0.105 | 0.158 | 0.118 |
| p95 nearest-rank, seconds | 0.134 | 0.180 | 0.139 |

| Класс | Correct C | Accuracy C |
|---|---:|---:|
| BUG_FIX | 2/10 | 20% |
| FEATURE | 5/10 | 50% |
| TEST | 10/10 | 100% |
| DOCS | 10/10 | 100% |
| REFACTOR | 3/10 | 30% |
| NEED_INPUT | 10/10 | 100% |

| Язык | Correct A | Correct B | Correct C |
|---|---:|---:|---:|
| EN | 0/36 | 0/36 | 26/36 (72.22%) |
| RU | 0/24 | 0/24 | 14/24 (58.33%) |

B→C: improved 40, regressed 0, both_correct 0, both_wrong_changed_raw 20, both_wrong_same_raw 0.
Сумма 60, прирост 40/60 = 66.67 percentage points. Exact two-sided McNemar p =
`1.8189894035458565e-12` для этой пары выборок. Поскольку B = 0 correct, ноль регрессий — floor effect,
а не доказательство безопасности модели в production.

Train loss 4.691650390625 → 0.10673856735229492;
validation loss 6.581140041351318 → 0.17431244254112244.
Owner-reported training routine — 77.79578466597013 s (~77.8 s); source timer включает
load/train/save/reload и проверки, не только GPU compute. Adapter saved/reloaded: TENSOR_IDENTICAL.
Уменьшение loss само по себе не доказывает generalization и не заменяет classification accuracy.

## Ограничения и состав

Все 60 ответов A и 59/60 B достигли LENGTH 12; один B завершился EOS. Обе arm дали 0 строгих меток.
Это слабый frozen prompt baseline. Лимит/prompt/postprocessing не менялись после результатов;
эксперимент не устанавливает превосходство над более сильным prompting или другими моделями.
C всё ещё ошибается 20/60 раз, особенно BUG_FIX и REFACTOR. Eval мал, сбалансирован и synthetic/
owner-curated; 10/10 в трёх классах не означает общей 100% надёжности. Family/rights/human evidence
не пересматривались Work независимо. Полная confusion matrix в aggregate handoff не приложена;
её значения не восстанавливались из неполных данных.

Latency исключает model load и измеряет generation от tokenized-input readiness до device sync.
Разные длины ответов ограничивают сравнение; меньшая сумма C не гарантирует ускорение.
Денежная стоимость запроса, API charges и электричество не измерялись; финансовой экономии не заявлено.
Исторический P9R4 остаётся SUSPENDED/HOLD; owner-local residual-risk consent не native custody proof.

Каталог содержит только 19 allowlisted source/test/prompt/policy/docs файлов. Dataset/eval, gold,
per-item predictions, owner forms/paths/hashes, adapter/model weights и raw logs не публикуются.
Без приватного submission route доступность dataset и adapter преподавателю ещё не подтверждена:
experiment execution accepted не означает окончательно закрытую course submission.

## Безопасная проверка публичного исходника

Из корня репозитория:

```sh
cd day-07
python3 -B -m unittest discover -s tests -v
python3 -B run.py synthetic-smoke
```

Staging-проверка: 100 cases, 88 PASS, 12 explicit SKIP, 0 failures/errors. 11 SKIP требуют
непубликуемый candidate corpus; ещё 1 — original generator reference. SKIP не считаются PASS.
Synthetic smoke — actual workflow с artificial human/ML test doubles, не повтор owner-эксперимента.
Code/tests/prompt/policy побайтово совпадают с R2; изменены только пять Markdown docs.
Исторические offline NOT_RUN состояния в source не переписывались; текущие результаты выше —
последующий owner report. Новые реальные owner/inference/train/Git действия не разрешены.

См. [English summary](SUMMARY_EN.md), [T00–T17](REQUIREMENTS_MATRIX.md),
[reproducibility](REPRODUCIBILITY_RU.md), [publication boundary](PUBLICATION_ALLOWLIST_RU.md).
