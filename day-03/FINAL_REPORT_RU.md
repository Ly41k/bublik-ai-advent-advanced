# Бублик — Day 3 / Final Candidate r2

Task ID: BUBLIK-D3-FINAL-ASSEMBLY-R2. **Level 1 PASS; Level 2 PASS; Course Minimum PASS по принятым evidence.** Финальный candidate передаётся на независимый Control Review. Сборка выполнена offline: без новых моделей, тестов, Playwright MCP и изменений production.

Baseline/HEAD: `6d0a0d73ba535b947a88eb08e5f54044ce6f9582`. Branch: `feat/day-03-course-minimum`. Candidate не закоммичен; его точные байты задаёт [SHA256_MANIFEST.json](SHA256_MANIFEST.json). Commit/push/PR/merge не выполнялись. Day 4 не начат.

| Gate | Итог | Evidence |
|---|---|---|
| 0 Preflight | PASS | Work окружение + принятый Mac preflight/реальный browser smoke |
| 1 Minimal UI | PASS | неизменная реализация r1 + три Mac сценария |
| 2 Agent Code Testing | PASS | первый pytest 11/11, exit0 |
| 3 Agent UI Smoke | PASS | UI-01/02/03, 31 MCP call, 9 PNG шагов |
| 4 Unified Flow | PASS | Code Work → UI Mac → Report r2, связанная доказательная цепочка |
| 5 Local Delivery | PASS | integrity, protected files, privacy, links, manifest |

## Входы и целостность

Оба исходных ZIP совпали с утверждёнными SHA256:

- r1: `418abe3d7d60309122c3f0926912b0da43853ccd5cc88ba4a675cb5b3bcf370b`.
- Mac: `e5030fba47ededc019e88abab8bc2173bf2c0f387762f45368f0a12159380d10`.

[Input integrity](evidence/assembly/input-integrity.json): безопасные пути/типы, отсутствие дубликатов и case-collisions, CRC PASS. Исходный r1 manifest **93/93 PASS**, точная inventory. Mac SHA256SUMS **9/9 PASS** (покрывает девять PNG, не все 44 файла Mac ZIP). Все 44 исходных Mac файла перенесены без изменения байтов под `evidence/mac/`. Общий финальный manifest покрывает также MCP records, reports и дополнительный preflight.png.

## Level 1 — Code Testing

[Code agent report](evidence/code/agent-report.md), [JSON](evidence/code/agent-report.json), [самостоятельный выбор](evidence/code/selection.json), [анализ](evidence/code/analysis.md).

| Реальный модуль | Пробел поведения | Новый файл |
|---|---|---|
| bublik.api.dependencies | неправильная конфигурация сервиса и HTTP500 | app/tests/test_d3_dependencies.py |
| bublik.application.service | ошибки repository и валидация до чтения | app/tests/test_d3_service_failures.py |
| bublik.infrastructure.memory_repository | параллельные операции с разными ID и сохранность соседей | app/tests/test_d3_memory_concurrency.py |

Первый настоящий запуск: **11/11 PASS, exit code 0**. [Первый stdout](evidence/code/first-run/stdout.txt), [stderr](evidence/code/first-run/stderr.txt), [команда/exit/SHA](evidence/code/first-run/result.json), [JUnit](evidence/code/first-run/junit.xml), [исходный prompt](prompts/code-testing.txt). Генерация сохранена в `evidence/code/first-run/generation/tests/`. Все эти байты неизменны относительно r1. Генерация и тесты заново не запускались.

Полная исходная Work регрессия **121/121 PASS**, Ruff PASS: [pytest log](evidence/final/pytest.stdout.txt), [pytest result](evidence/final/pytest.json), [Ruff log](evidence/final/ruff.stdout.txt). Это исторические результаты r1, а не проверки сборки r2. r1 также сохраняет подготовительный baseline FAIL из-за отсутствующей package metadata, затем baseline 110/110 PASS. После исторического первого запуска в r1 исправлялся только порядок импортов main.py; первоначальный main сохранён. r2 production не меняет.

## Level 2 — принятый Mac UI Smoke

Решение Control: **MAC_UI_SMOKE_ACCEPTED**. [Mac report](evidence/mac/replay-mac-001/evidence/SMOKE_REPORT_RU.md), [Mac JSON](evidence/mac/replay-mac-001/evidence/smoke-results.json), [исходный screenshot manifest](evidence/mac/replay-mac-001/evidence/SHA256SUMS). Реальный сервер `playwright-day3`, Firefox/156.0, localhost:8003. Три исходных сценария v1.0.0 не изменены.

Выполнены 31 реальный MCP-вызов и 9 шагов. Ниже ссылки на исходные PNG и MCP record каждого шага. В JSON сохранён полный список вызовов шага; указанная в таблице запись — screenshot call.

| Сценарий / шаг | Assertion | MCP screenshot record | PNG |
|---|---|---|---|
| UI-01 / 1 | PASS: Task title и Create присутствуют; список Tasks пуст. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/004.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-01/step-01.png) |
| UI-01 / 2 | PASS: Значение Task title равно UI-01 Bublik task. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/007.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-01/step-02.png) |
| UI-01 / 3 | PASS: Ровно одна listitem, title UI-01 Bublik task, status todo. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/010.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-01/step-03.png) |
| UI-02 / 1 | PASS: Отображаемый список Tasks пуст. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/013.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-02/step-01.png) |
| UI-02 / 2 | PASS: Значение Task title равно UI-02 Bublik task. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/016.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-02/step-02.png) |
| UI-02 / 3 | PASS: Одна задача UI-02 Bublik task, status todo; task ID f2bae8cd-f73f-40b7-af0a-da1b2cdca882. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/020.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-02/step-03.png) |
| UI-02 / 4 | PASS: Та же задача и ID f2bae8cd-f73f-40b7-af0a-da1b2cdca882; title сохранён, status done, Mark done disabled=true. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/024.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-02/step-04.png) |
| UI-03 / 1 | PASS: Пустое поле Task title и ноль строк Tasks. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/027.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-03/step-01.png) |
| UI-03 / 2 | PASS: Alert: Task title must contain 1–200 characters.; ноль строк Tasks; POST /tasks => [422] Unprocessable Content. | [call](evidence/mac/replay-mac-001/evidence/mcp-calls/031.json) | [PNG](evidence/mac/replay-mac-001/evidence/screenshots/UI-03/step-02.png) |

**9/9 SHA256 шагов PASS; все 10 PNG читаются**, включая сохранённый оригинальный [preflight.png](evidence/mac/replay-mac-001/evidence/screenshots/preflight.png). Preflight не считается десятым smoke-шагом. Совпадение хеша двух одинаковых пустых страниц не означает повторное использование вызова: сохранены отдельные screenshot calls 004 и 027.

UI-03: [network call 030](evidence/mac/replay-mac-001/evidence/mcp-calls/030.json) подтверждает ожидаемый HTTP422. Отсутствие создания проверено в границах сценария: ноль строк UI + 422; API списка не добавлялся. UI-02 read-only DOM calls 019/023 подтверждают тот же task ID и done/disabled. Snapshots встроены в оригинальные browser_snapshot records.

## Исторические ошибки и перенос

Первоначальный Work `listen EPERM` остаётся в [navigation error](evidence/preflight/browser-health.json), [screenshot error](evidence/preflight/screenshot-attempt.json) и [исходном r1 report](evidence/history/r1/FINAL_REPORT_RU.md). Ошибка среды Work не исправлялась и не исследовалась повторно. Обязательные UI-сценарии завершены отдельным принятым Mac-запуском.

Mac `git status --short`, exit128 — дополнительная проверка распакованного каталога без `.git`, не дефект UI. Оригинальная ошибка сохранена в Mac JSON/report. Day 1/2 проверены отдельно в действительном checkout: [Git scope r2](evidence/assembly/git-scope-r2.json), 269/269 blob SHA совпали; изменений вне day-03/ нет.

## Единый workflow и поставка

[AGENT_WORKFLOW_RU.md](AGENT_WORKFLOW_RU.md) описывает воспроизводимый агентный вызов Code → MCP UI → Report. Текущая цепочка использует принятые Work и Mac этапы; r2 только связывает их. Единый новый непрерывный runtime не заявляется. [REPORT.json](REPORT.json) связывает baseline, сценарии/SHA, code first-run, MCP records и PNG. [Матрица](REQUIREMENTS_RU.md) показывает PASS всех обязательных критериев.

[Preservation verification](evidence/assembly/preservation-verification.json) подтверждает неизменность app, tests, scenarios, исторических logs и всех Mac bytes. Оригинальные обновлённые r1 документы сохранены в `evidence/history/r1/`, а manifest — побайтно как `SHA256_MANIFEST_r1.json` в том же каталоге. Имя уточнено для совместимости с неизменённым r1 verifier; input-integrity содержит source-path mapping. [Privacy](PRIVACY_REPORT_RU.md) и [link verification](evidence/assembly/link-verification.json) входят в поставку. README содержит команды воспроизведения и manifests. Результаты сборки/хеширования не выдаются за новый тестовый прогон.

## Остающиеся ограничения

- Финальный r2 ожидает независимого Control Review; публикация не разрешена.
- Этапы выполнены в Work и Mac, без нового общего запуска; дальнейшее воспроизведение требует соответствующего окружения.
- Некоторые tool messages ссылаются на runtime `.playwright-mcp/*.yml`, которых нет в Mac ZIP. Проверяемые snapshots сохранены inline в browser_snapshot records.
- Связь Mac запуска с r1 и Mac preflight приняты решением Control; отдельный production SHA и отдельный текстовый preflight log в Mac ZIP не поставлялись. Исходный preflight PNG сохранён.
- Work EPERM и Mac Git128 сохранены как исторические факты. Открытых Course Minimum блокеров после MAC_UI_SMOKE_ACCEPTED нет.

После сборки работа остановлена на локальном candidate. Новых моделей, pytest, Playwright, изменений production и Git publication actions не было.
