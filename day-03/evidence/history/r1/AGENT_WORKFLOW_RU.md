# Unified Testing Flow — v1.0.0

Один вызов в Work Chat из корня репозитория:

> Выполни day-03/AGENT_WORKFLOW_RU.md как TestingReportAgent. Обязательные входы: app_root=day-03/app, baseline_sha=6d0a0d73ba535b947a88eb08e5f54044ce6f9582, Python 3.13.3, реальный Playwright MCP, evidence_root=новый каталог попытки. Верни Markdown + JSON report. Commit/push/PR/merge запрещены.

Это агентный workflow: агент принимает решения по реальному коду и MCP-ответам. Локальные Python-скрипты сохраняют evidence; они сами не генерируют тесты и не заменяют модель. Отдельная оркестрационная платформа не требуется.

1. Проверить входы, Git SHA, зависимости и доступность браузера MCP. При отсутствии обязательного входа вернуть `BLOCKED / MISSING_REQUIRED_INPUT`, без угадывания.
2. До генерации проверить старые тесты и окружение. Изучить `app/src/bublik` и старые тесты. Прочитать `prompts/code-testing.txt`. Самостоятельно выбрать минимум три реальных модуля с пробелами поведения. Сохранить `analysis.md`, `selection.json` и исходный prompt до генерации.
3. Создать три новых тестовых файла. Сохранить точную генерацию и SHA. Первый запуск выполнить через `scripts/run_code_tests.py`, указав новый `--run-dir` и ровно эти файлы. Нельзя запускать новые тесты заранее, подменять первый FAIL повторным PASS или менять production ради тестов. Из существующего candidate тесты уже сгенерированы: их повторный запуск является replay, а новая генерация требует новой попытки и нового каталога.
4. Запустить приложение и настоящий Playwright MCP по README. Выполнить ровно `scenarios/UI-01.md`, `UI-02.md`, `UI-03.md`. Через MCP навигировать, вводить, нажимать, проверять DOM/snapshot и сохранять PNG после каждого шага. Следующий вызов выбирать по фактическому ответу. Проверки можно выполнить read-only через `browser_evaluate`; запрещены подмена DOM, mock API и прямые HTTP вместо UI. Записывать каждую пару JSON-RPC `tools/call` → response. При недоступном браузере сохранить диагностику, отметить сценарии `BLOCKED / NOT_RUN`, не создавать поддельные изображения.
5. Собрать Markdown и JSON: baseline/HEAD SHA, SHA исходников и тестов, версии/хеши сценариев, команды, первый exit code, stdout/stderr, UI assertions, MCP records, пути PNG, ошибки и вероятные компоненты. Единый PASS возможен только при полном доказательстве обоих уровней. Любой обязательный BLOCKED блокирует Course Minimum PASS.
6. Проверить неизменность Day 1/2, privacy, SHA manifest и архив. Остановиться на локальном candidate для Control.

Текущая попытка инициирована одним заданием `BUBLIK-D3-COURSE-MINIMUM` в Work Chat. Code Testing делегирован одному `CodeTestingReportAgent` с контрактом `prompts/code-agent-contract.md`; UI preflight выполнен основным агентом через настоящий stdio Playwright MCP. Полная цепочка до UI PASS в этой среде не завершена: см. FINAL_REPORT_RU.md.
