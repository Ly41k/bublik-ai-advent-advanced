# Матрица Day 2 Profiles

Обязательные пункты ниже — пересказ сохранённого оригинала задания, а не новое
толкование по памяти. SHA оригинала указан в
`evidence/teacher-assignment-source.json`. Дополнительные требования пользователя
помечены U; необязательное усиление вынесено отдельно.

| ID | Критерий преподавателя | Реализация и evidence | Статус в candidate |
|---|---|---|---|
| T01 | Два переключаемых профиля агентного режима | `profiles.py`, две instruction families; реальные `thread/start`, ledger Turns 1–10 | HISTORICAL_TECHNICAL_PASS; public native transport excluded |
| T02 | Bug Fix находит причину, исправляет и проверяет последствия | Turns 1–2; `app/src/bublik/domain/task.py`, regression, native RED/GREEN, historical Mac Gate | SAVED_PATCH_PASS; original executions FAIL |
| T03 | Research исследует код и даёт структурированный ответ | Turns 3, 5, 8–10; `research/`; решение пользователя о v4 | RESEARCHER_V4_TECHNICAL_PASS / USER_ACCEPTED; receipt MISSING сохраняется |
| T04 | Инструкция для каждой роли | `profiles/common.md`, `bug_fix_engineer.md`, `researcher.md`; version hashes сверены с реальными RPC | PASS_AS_DEVELOPER_INSTRUCTIONS; системная роль не заявляется |
| T05 | Описаны обязательные действия, в том числе проверки | Bug Fix требует collection/RED/fix/GREEN/Gate; Research требует reading/citations | SOURCE_PASS; stop-on-error и исторические отказы сохранены |
| T06 | Описаны запреты каждой роли | Только два разрешённых fix-файла; read-only Research; запрет самовольных dependencies/config changes | SOURCE_PASS; не заменяет свежий native enforcement |
| T07 | Форматы ответов Bug Fix и Research | Instructions + десять task-only сохранённых ответов; prefix, answer, sources, limitations, document | HISTORICAL_TECHNICAL_PASS |
| T08 | Реальный Bug Fix с рабочим результатом первого запуска | Native fix + regression есть; Attempts 1–2 original FAIL/BLOCKED | FIRST_RUN_NOT_DEMONSTRATED; требует решения принимающего ревьюера |
| T09 | Реальный вопрос по проекту для Research | Где хранятся задачи, как связан repository port, DI и restart, что потребуется для будущего хранения | PASS_REAL_QUESTION; будущая SQLite-реализация не выполнялась |
| T10 | После неуспеха профиль доработан и проверен снова | `ITERATIONS_RU.md`, v1–v4, реальные последующие turns; v5 только offline | PASS_DOCUMENTED_ITERATIONS; profile и harness fixes различаются |
| T11 | Два готовых профиля с инструкциями | Текущие public instruction exports Bug Fix v3 / Researcher v4; версии и исходники parser | SOURCE_DELIVERED; Researcher v4 USER_ACCEPTED; не самостоятельный public live runner и не финальный PASS всего Day 2 |
| T12 | Logs/screenshots успешного первого выполнения | Реальные sanitized native RED/GREEN logs и task-only ответы; original PNG SHA в реестре | LOGS_DELIVERED; literal clean-first-run OPEN; оригиналы screenshot исключены по privacy |
| T13 | Описаны доработки после первой попытки | Отдельная таблица profile/runtime/harness iterations; FAIL/BLOCKED сохранены | PASS_DOCUMENTED |

| ID | Дополнительное требование пользователя/Control | Фактическое evidence | Статус |
|---|---|---|---|
| U01 | Наблюдаемое переключение tester/researcher с общей историей | `switch-history-restart.json`; Turn 7 tester v3 → Turn 8 researcher v3; точные instruction SHA | PASS_HISTORICAL; публичный metadata projection |
| U02 | Восстановление выбранного профиля и полной истории после restart | PID 92956 → 93237, Turn 9 researcher; 30 visible replay events; точное сравнение всех 10 replay | PASS_EXISTING_EVIDENCE; не глобальный Codex state и не app RAM persistence |
| U03 | Согласованный характер Researcher и human signoff | V3 historical NOT_ACCEPTED; V4 Technical PASS / User ACCEPTED по окончательному решению; v5 DEFERRED / NOT_RUN | CLOSED_BY_EXPLICIT_V4_USER_ACCEPTANCE; дополнительные испытания не нужны |
| U04 | Точные source SHA/цитаты, JSON/Markdown | Проверены 9 ссылок Turn 3 и 6 Turn 10; Python AST ownership, Markdown exact quote; original document совпал | PASS_CURRENT_OFFLINE_CONTENT_AUDIT |
| U05 | Восемь конкретных кадров | В существующем A38 8 основных + 2 appendix; это ручные снимки позднего просмотра истории | ORIGINALS_EXCLUDED; logs доступны, live-first-run не доказан |
| U06 | Day 1 неизменён, публикация только после разрешения | Пакет содержит только новый `day-02/`; remote main зафиксирован; Mac index audit остаётся историческим | DELIVERY_SCOPE_PASS; staging проверен в отдельном Work checkout; Mac checkout NOT_CHECKED |
| U07 | Бюджет, сохранение неуспехов, нет повторов | 10 turns сверены с main и budget hash chains; новые calls 0, текущий лимит 10/11 | PASS_ASSEMBLY_SCOPE |
| U08 | Native security-gate, ACL и восстановление исторических данных | В данную сборку не исполняются и не включаются временные forensic bundles | DEFERRED; не PASS |

Необязательное усиление: третий профиль и его проверка — **DEFERRED**, вне Course
Minimum. Две версии одной роли и Discussion не считаются дополнительными ролями.

Researcher v4 принят пользователем. Researcher v5 DEFERRED / NOT_RUN, Turn 11 CANCELLED. Решение этой сборки: **candidate подготовлен; Course Minimum PARTIAL / BLOCKED до финального решения Control**.
Решение преподавателя по достаточности итераций и решение Control о поставке
не выводятся автоматически из технических PASS.
