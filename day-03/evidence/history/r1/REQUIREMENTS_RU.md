# Day 3 — Requirements / приёмка

Итог Course Minimum: **BLOCKED**. Формальный acceptance result: **FAIL**, поскольку обязательный Level 2 не выполнен. FAIL здесь не означает провал новых code tests.

| Требование | PASS/FAIL | Evidence / ограничение |
|---|---|---|
| Baseline SHA и локальная feature branch | PASS | evidence/preflight/git.json |
| Python 3.13.3, locked deps, запуск FastAPI | PASS | environment.json; app.stdout-stderr.txt |
| Рабочий браузер и сохранение PNG через MCP | FAIL (BLOCKED) | browser-health.json; screenshot-attempt.json: EPERM |
| Минимальная независимая копия + /ui | PASS (реализация) | app/src/bublik/main.py; ui.html |
| Работа UI в настоящем браузере | FAIL (NOT_VERIFIED) | браузер не запущен |
| Самостоятельный анализ агентом 3 модулей | PASS | evidence/code/analysis.md; selection.json |
| 3 новых отдельных test files | PASS | app/tests/test_d3_*.py |
| Первый запуск новых тестов PASS | PASS | first-run/stdout.txt: 11 passed, exit 0 |
| Prompt, выбор, генерация, команда, stdout/stderr/exit | PASS | prompts/; evidence/code/first-run/ |
| UI-01 Create Task через MCP | FAIL (BLOCKED / NOT_RUN) | scenarios/UI-01.md |
| UI-02 Update Task через MCP | FAIL (BLOCKED / NOT_RUN) | scenarios/UI-02.md |
| UI-03 Validation через MCP | FAIL (BLOCKED / NOT_RUN) | scenarios/UI-03.md |
| PNG каждого шага | FAIL (BLOCKED) | 0 PNG; ожидается минимум 9 |
| PASS/FAIL и диагностика | PASS | REPORT.json; preflight/diagnostics.json |
| Один документированный агентный workflow | PASS (документ) | AGENT_WORKFLOW_RU.md |
| Полный успешный unified flow | FAIL (BLOCKED) | end_to_end_completed=false |
| Привязка к commit/scenario/hash/path | PASS | REPORT.json + SHA256_MANIFEST.json |
| Day 1/2 и старые тесты неизменны | PASS | source-copy-comparison.json; Git verification |
| GitHub-safe partial candidate, manifest, privacy | PASS (поставка) | SHA256_MANIFEST.json; PRIVACY_REPORT_RU.md |
| Полная поставка с настоящим UI evidence | FAIL (BLOCKED) | отсутствуют UI executions/PNG |
| Не выполнять commit/push/PR/merge | PASS | HEAD остаётся baseline; только day-03/ untracked |
