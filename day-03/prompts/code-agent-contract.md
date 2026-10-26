# CodeTestingReportAgent — контракт v1
Обязательные входы: app_root, baseline_sha, interpreter, prompt_path, runner_path, evidence_root.
При отсутствии любого входа: немедленно вернуть JSON со status=BLOCKED, error=MISSING_REQUIRED_INPUT; не угадывать и не вызывать инструменты.
app_root: /workspace/scratch/b0d13eb0cb28/bublik-ai-advent-advanced/day-03/app
baseline_sha: 6d0a0d73ba535b947a88eb08e5f54044ce6f9582
interpreter: /workspace/scratch/b0d13eb0cb28/.venv313/bin/python
prompt_path: day-03/prompts/code-testing.txt
runner_path: day-03/scripts/run_code_tests.py
evidence_root: day-03/evidence/code
Выход: JSON report в evidence/code/agent-report.json и Markdown report там же.
Выбрать самостоятельно 3 реальных модуля после изучения исходников и существующих тестов. Указать конкретные пробелы поведения; 100% line coverage не означает полное покрытие поведения.
До генерации сохранить analysis.md и selection.json. Создать ровно 3 новых файла tests/test_d3_*.py. Production и существующие тесты не менять. Без установки, сети, других агентов и Git mutations.
Первый запуск только через run_code_tests.py --app ... --run-dir .../first-run tests/test_d3_....py (три выбранных файла). Не использовать pytest collect, тестовые прогоны или импорт новых тестов заранее. Первый результат неизменяем; при FAIL не повторять для замены evidence.
Сохранить prompt verbatim, выбор, команды исследований (без приватных journals), генерацию и stdout/stderr/exit code. Результат не означает весь Day 3 PASS.
