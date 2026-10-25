# Бублик — Day 2: Profiles / Course Minimum candidate r2

**Статус: PARTIAL / BLOCKED, не финальный PASS.**

Два профиля созданы и использованы на реальных задачах: Bug Fix Engineer и
Researcher. Пакет объединяет существующие исходники и проверенные выдержки
исторических evidence. Новых вызовов модели, Codex или native sandbox при сборке
не было. Текущий бюджет: **10/11**; Turn 11 **CANCELLED**, дополнительных испытаний не требуется.

Основа GitHub: [`main` — 3c2ed09a2e5c9e35a70e18b11dfe0a29a675db66](https://github.com/Ly41k/bublik-ai-advent-advanced/commit/3c2ed09a2e5c9e35a70e18b11dfe0a29a675db66).
В нём опубликован Day 1; каталога `day-02/` ещё нет. Исторический Mac working
tree не объявляется текущим и не подменяется состоянием remote. Поставка
добавляет только `day-02/`; Day 1 и корневой baseline не изменяются.

| Часть | Реально подтверждено | Ограничение |
|---|---|---|
| Bug Fix | Модель создала fix `Task.status` и regression; native RED 10 failed / 3 passed; GREEN 13 passed | Первые два original executions — FAIL / model BLOCKED; чистый успешный first run не доказан |
| Research | Исследование хранения, DI и срока жизни данных; Markdown и проверяемые источники | Turn 3: model PASS, original host execution FAIL; отдельная проверка сохранённого результата PASS |
| Более поздний Research | Turns 5, 8, 9 и 10 original PASS | Техническая оценка не заменяет человеческую оценку стиля |
| Switch/history/restart | 10 фактических RPC replay сверены с предшествующей видимой историей; смена профилей; restart процесса консоли | Приватные полные журналы не публикуются; скрытое состояние сервера не утверждается |
| Researcher v4 | **Technical PASS / User ACCEPTED**, решение пользователя от 25.10.2026 | Receipt Turn 10 остаётся MISSING; прежняя editorial PARTIAL сохранена как историческая оценка |
| Researcher v5 | **DEFERRED / NOT_RUN**; существующий offline candidate сохранён | Дополнительный model turn не требуется; Turn 11 CANCELLED |

История original executions: **FAIL, FAIL, FAIL, FAIL, PASS, FAIL, PASS, PASS,
PASS, PASS**. Независимые проверки сохранённых результатов не меняют эти статусы.
Существовавшие неудачные attempts и причины доработок изложены в
[ITERATIONS_RU.md](ITERATIONS_RU.md); полная привязка —
[evidence/ten-turn-ledger.json](evidence/ten-turn-ledger.json).

Решение пользователя: [Researcher v4 ACCEPTED](decisions/RESEARCHER_V4_ACCEPTED_2026-10-25.json). Оно закрывает критерий принятия Researcher для Course Minimum, но не меняет исторические FAIL/BLOCKED и не является финальным PASS всего Day 2.

## Что смотреть преподавателю и Control

- [Матрица обязательных и дополнительных требований](REQUIREMENTS_RU.md).
- [Профили, инструкции, переключение и ограничения запуска](USAGE_RU.md).
- [Исторический Bug Fix: native RED/GREEN](evidence/bugfix/red-green.json),
  [diff](evidence/bugfix/task-status-fix.diff),
  [regression](app/tests/test_task_status_invariant.py).
- [Реальный Markdown Research Turn 3](research/storage-research-turn03.md),
  [ответ Researcher v4 / Turn 10](research/researcher-v4-turn10-answer.md),
  [проверенные источники](research/SOURCES_RU.md).
- [Фактические switch/history/restart события](evidence/switch-history-restart.json).
- [Неподтверждённые критерии и отложенная работа](UNCONFIRMED_RU.md).
- [Исключённые приватные файлы и sanitization](PRIVACY_RU.md).
- [Минимальный staging plan](PUBLICATION_PLAN_RU.md) и
  [проект описания Draft PR](DRAFT_PR_RU.md).
- [Результат проверки candidate](ASSEMBLY_REPORT_RU.md).

`app/` — отдельная Day 2 копия учебного сервиса с существующим принятым patch,
а не изменение `day-01/app/`. Сравнение с Day 1 перечисляет все различия копии,
включая собственные Day 2 Rules/tool configuration. Существующие `app/README.md`
и comments baseline сохранены как source; текущий статус задаёт этот README.

Публичные logs и ответы — явно обозначенные task-only projections. В них удалены
локальные machine paths и контрольные маркеры частной истории; original SHA
и правила преобразования сохранены. Они не выдаются за побайтные оригиналы.
Подлинные Terminal screenshots показывают поздний просмотр сохранённых evidence,
а не live capture первого запуска. Их оригиналы с приватными путями исключены;
вместо них приложены безопасные logs.

SQLite/ACL research, historical recovery и native security-gate — DEFERRED
решением Control. Третий профиль — необязательное усиление, DEFERRED.
Эта сборка не меняет соответствующие ограничения и не разрешает Day 3.

В отдельном Git checkout от указанного main подготовлен staging только `day-02/`; состояние Mac checkout не проверялось. Полный status, staged list и результаты проверки находятся в `control-review/` внешнего review ZIP. Commit, push, PR и merge не выполнялись. Candidate остановлен для независимого Control review и отдельного разрешения публикации.
