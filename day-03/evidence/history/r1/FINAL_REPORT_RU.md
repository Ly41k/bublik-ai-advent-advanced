# Бублик — Day 3 / FINAL_REPORT_RU

Task ID: BUBLIK-D3-COURSE-MINIMUM. Candidate r1. **Course Minimum BLOCKED; подготовлен локальный PARTIAL candidate.**

Baseline и HEAD: `6d0a0d73ba535b947a88eb08e5f54044ce6f9582`. Branch: `feat/day-03-course-minimum`. Candidate не закоммичен: его точная версия задаётся SHA manifest, отдельного candidate commit SHA нет. Day 1/2 не изменены. Commit/push/PR/merge не выполнялись.

| Gate | Итог | Основание |
|---|---|---|
| 0 Fast Preflight | BLOCKED | SHA, Python, FastAPI готовы; браузер MCP запрещён средой |
| 1 Minimal UI | PARTIAL | HTML/API/JS precheck PASS; реальный UI не проверен |
| 2 Agent Code Testing | PASS | 3 модуля, 3 файла, первый pytest 11/11, exit 0 |
| 3 Agent UI Smoke | BLOCKED | UI-01/02/03 NOT_RUN, 0 PNG |
| 4 Unified Testing Flow | PARTIAL | workflow и общий отчёт есть; полная цепочка не завершена |
| 5 Delivery | PARTIAL | проверяемый GitHub-safe candidate; UI evidence отсутствует |

## Code Testing

Один CodeTestingReportAgent получил исходный prompt и строгий контракт входа/выхода. До генерации изучил существующий код/тесты и сохранил выбор. Выбранные пробелы:

| Модуль | Обоснование | Новый файл |
|---|---|---|
| bublik.api.dependencies | Неправильная конфигурация сервиса и HTTP 500 | app/tests/test_d3_dependencies.py |
| bublik.application.service | Передача ошибок repository и валидация до чтения | app/tests/test_d3_service_failures.py |
| bublik.infrastructure.memory_repository | Параллельное сохранение разных ID и замена без потери соседей | app/tests/test_d3_memory_concurrency.py |

Первый настоящий запуск: **11 passed in 0.05s, exit code 0**. Лог: `evidence/code/first-run/stdout.txt`; stderr: `stderr.txt` (пустой); точная команда, время, SHA генерации и production: `result.json`; JUnit: `junit.xml`. Все пути в этом абзаце, кроме первого, относительно `evidence/code/first-run/`. Генерация сохранена в `generation/tests/`. До первого запуска новые тесты не исполнялись/не импортировались/не collect. После него тесты не менялись.

Production не менялся во время генерации и первого запуска. При финальной проверке исправлен только порядок импортов main.py; исходный main сохранён в `evidence/code/production-at-first-run/src/bublik/main.py`. Последующая регрессия: **121/121 PASS**, Ruff PASS. Исторический first-run не перезаписан и остаётся отдельным evidence.

До генерации был начальный baseline FAIL (101 passed, 9 failed) из-за отсутствующей metadata установленного пакета. После штатной editable-установки baseline **110/110 PASS**, затем скопированные существующие тесты Day 3 **110/110 PASS**. Все три лога сохранены в `evidence/preflight/`; подготовительный FAIL не скрыт и не является первым запуском новых тестов.

## UI и реальный MCP

Добавлена одна страница `/ui`: Task title, Create, строки title/status, Mark done, видимая ошибка. Бизнес-логика и существующие API скопированы из Day 2. HTTP precheck: HTML 200, создание todo, обновление/чтение done, пустой title → 422. JavaScript прошёл node --check. Эти проверки не доказывают UI smoke.

Стандартно установлен `@playwright/mcp@0.0.83`. Chromium не скачался (невалидный ZIP); Firefox и FFmpeg скачались штатно. Настоящий stdio MCP: `initialize` PASS, `tools/list` PASS. Два настоящих `tools/call` — browser_navigate и browser_take_screenshot — получили `isError=true`: `listen EPERM: operation not permitted` при создании внутреннего Unix-сокета Playwright. Вероятный компонент: **ограничение среды запуска браузера/MCP**, а не проверенный дефект приложения.

| Сценарий v1.0.0 | Итог | MCP steps / assertions | PNG |
|---|---|---|---:|
| UI-01 Create Task | BLOCKED / NOT_RUN | не выполнялись | 0 |
| UI-02 Update Task | BLOCKED / NOT_RUN | не выполнялись | 0 |
| UI-03 Validation | BLOCKED / NOT_RUN | не выполнялись | 0 |

Всего **0 screenshots**, пути отсутствуют. Ожидаемые пути после реального выполнения: `evidence/screenshots/UI-01/step-01..03.png`, `UI-02/step-01..04.png`, `UI-03/step-01..02.png` (всего минимум 9). Это планируемые пути, не существующие evidence. Реальные MCP запросы/ответы находятся в `evidence/preflight/mcp-initialize.json`, `mcp-tools.json`, `browser-health.json`, `screenshot-attempt.json`. Они являются preflight evidence и не выдаются за выполнение сценариев.

## Поставка и следующий шаг

README содержит команды установки/воспроизведения. AGENT_WORKFLOW_RU.md описывает единый агентный вызов; REPORT.json связывает результаты с baseline, версиями и SHA сценариев. SHA256_MANIFEST.json покрывает все поставляемые файлы кроме самого manifest. scripts/verify_candidate.py проверяет байты и согласованность evidence без повторного pytest. Privacy report описывает проверку состава. Архив содержит только day-03/, без .git, venv, node_modules, caches и credentials.

Открыт один блокер: **D3-BROWSER-MCP-EPERM**. Следующий шаг для Control — выбрать среду, где стандартный Playwright MCP может запустить браузер и создать свой внутренний сокет; затем выполнить три существующих сценария с реальными PNG и обновить отчёты. Существующий code first-run сохраняется; повторная генерация тестов для закрытия UI не нужна. Без настоящего UI evidence общий PASS запрещён.

Публикация остановлена на локальном candidate и требует следующего решения Control.
