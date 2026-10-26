# Day 3 — Requirements / Candidate r2

**Level 1 PASS; Level 2 PASS; Course Minimum PASS по объединённым принятым evidence.** Финальный r2 ожидает независимого Control Review. Новых тестовых прогонов при сборке не было.

| Критерий | Итог | Evidence / граница |
|---|---|---|
| Baseline и локальная feature branch | PASS | evidence/assembly/git-scope-r2.json |
| Минимальная независимая копия /ui и прежние API | PASS | app/src/bublik/main.py; ui.html — байты r1 |
| Level 1: самостоятельный анализ 3 реальных модулей | PASS | evidence/code/selection.json; analysis.md |
| Три новых отдельных test files | PASS | app/tests/test_d3_*.py — байты r1 |
| Первый настоящий pytest 11/11, exit0 | PASS | evidence/code/first-run/result.json; stdout.txt |
| Prompt, генерация, команда, stdout/stderr и exit | PASS | prompts/; evidence/code/first-run/ |
| Полная Work регрессия 121/121 и Ruff | PASS | evidence/final/pytest.stdout.txt; ruff.stdout.txt — исторические |
| Level 2: UI-01 Create Task через MCP | PASS | evidence/mac/replay-mac-001/evidence/smoke-results.json; mcp-calls/001.json … 010.json |
| Level 2: UI-02 Update Task через MCP | PASS | evidence/mac/replay-mac-001/evidence/mcp-calls/011.json … 024.json |
| Level 2: UI-03 Validation через MCP | PASS | evidence/mac/replay-mac-001/evidence/mcp-calls/025.json … 031.json; ожидаемый 422 |
| Настоящие MCP вызовы и PNG каждого шага | PASS | 31 запись; 9 PNG шагов; SHA256SUMS 9/9 |
| Assertions, PASS/FAIL и диагностика | PASS | Mac smoke-results.json; historical Work preflight |
| Единый workflow Code → MCP UI → Report | PASS | AGENT_WORKFLOW_RU.md; принятые этапы Work/Mac + offline assembly |
| Привязка SHA, версий сценариев и путей evidence | PASS | REPORT.json; SHA256_MANIFEST.json |
| Исходные manifests и безопасные ZIP paths | PASS | evidence/assembly/input-integrity.json |
| Protected Day 1/2 неизменны | PASS | evidence/assembly/git-scope-r2.json |
| GitHub-safe privacy и ссылки | PASS | PRIVACY_REPORT.json; evidence/assembly/link-verification.json |
| r2 без новых моделей/тестов/MCP/production changes | PASS | evidence/assembly/preservation-verification.json |
| Без commit/push/PR/merge | PASS | HEAD=baseline; r2 только локальный candidate |

Все Gate 0–5: PASS в объёме локального candidate. Успешный Mac smoke закрывает необходимую браузерную демонстрацию; первоначальный Work EPERM сохранён как исторический BLOCKED. Полный непрерывный прогон одной командой в одной среде не заявляется. Финальный review и публикация остаются за Control.
