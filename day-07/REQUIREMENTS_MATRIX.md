# Day 7 — критерии T00–T17 и фактический статус

Источник текущего выполнения: owner-reported Mac outputs, принятые Control 29.10.2026.
Work независимо проверил source integrity/public subset, но не приватный corpus, audit или ML-run.
EXPERIMENT_EXECUTION_ACCEPTED не означает FINAL_SUBMISSION/PUBLICATION_ACCEPTED.

| ID | Критерий | Evidence / граница проверки |
|---|---|---|
| T00 | Dataset для собственной задачи | Owner сообщил accepted 200 train / 40 valid; private artifacts не получены Work |
| T01 | Узкая повторяющаяся задача | Developer Task Router, фиксированные шесть меток labels-v1.1 |
| T02 | Определён верный ответ | Entire raw equals gold; scorer/policy неизменны; gold review OWNER-ATTESTED |
| T03 | Eval с эталонами | Existing 60, 36 EN/24 RU, owner review/freeze; закрытый eval не опубликован |
| T04 | Base без task instructions и с prompt | A user-only native template с generic system; B frozen prompt; обе arm 60/60 outcomes |
| T05 | Baseline до обучения | Owner сообщил A/B lock до train: strict correct 0/60 и 0/60; LIMIT 12 раскрыт |
| T06 | От 200 train, формат Day 6 | Accepted 200 train, отдельно 40 valid; три сообщения system/user/assistant |
| T07 | Существующие источники | 24 новых fact-inspired по публичным Day 6 docs; source-specific local rights OWNER-ATTESTED |
| T08 | Генерация/разметка нехватки | 216 новых synthetic; прозрачный origin, без заявлений о реальных logs/tickets |
| T09 | Train/valid и исключение eval | 14 400 cross pairs, 0 flags, owner scenario review; не independent proof Work |
| T10 | Удалить дубли/почти-дубли | 28 680 внутренних и 1 770 eval pairs, 0 flags; global/related review, semantic limits сохранены |
| T11 | Случайные 30 глазами | Owner: frame fixed, CSPRNG seed committed до draw, real 30/30 PASS, corrections 0; не 240 approvals |
| T12 | Проверить разброс | 40/class в 240; 144 EN/96 RU; source/origin/domain counts проверялись; synthetic balanced corpus ограничивает перенос |
| T13 | Единый ответ | Exact six-string whitelist; C format 60/60 против A/B 0/60; no strip/repair |
| T14 | Обучить свой dataset | Owner: один fresh LoRA, 150 iterations, ~77.8s, losses, save/reload TENSOR_IDENTICAL |
| T15 | Prompted base против tuned | B и C на тех же 60/prompt/decoding; B 0/60, C 40/60 |
| T16 | Сравнить результаты | Accuracy/format/macro-F1, class/language, paired counts, latency/loss; public aggregates OWNER-REPORTED |
| T17 | Dataset + trained model + сравнение | Эксперимент принят по owner evidence; dataset/adapter private, маршрут передачи преподавателю и публикация PENDING |

Нет повторного обучения, новых eval, исправления gold по ответам модели или замены protocol после
результатов. Исторические R2 offline NOT_RUN и P9R4 SUSPENDED/HOLD не переписаны. Текущая матрица
не утверждает независимый аудит всех 240, разрешение на dataset/adapter redistribution или готовый PR.
Полная confusion matrix не приложена к этому aggregate handoff и не была придумана Work.
