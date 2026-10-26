# Бублик — Day 3: Testing

Локальный candidate от `6d0a0d73ba535b947a88eb08e5f54044ce6f9582`. Публикация не разрешена. Уровни Code и UI PASS; финальный r2 ждёт независимого Control Review. Точный итог — в FINAL_REPORT_RU.md и REPORT.json.

Приложение скопировано из `day-02/app`; домен, сервис, HTTP API и repository сохранены. Добавлен только `GET /ui` с одной HTML-страницей и минимальным JavaScript. Перезапуск удаляет задачи; новая загрузка страницы показывает задачи, созданные в этой вкладке. API списка задач не добавляется.

## Подготовка

Из `day-03/`, с Python 3.13.3, uv и Node.js 24:

```bash
uv venv --python 3.13.3 .venv
uv pip install --python .venv/bin/python -r app/requirements.lock
uv pip install --python .venv/bin/python --no-build-isolation --no-deps -e app
npm ci --prefix browser
node browser/node_modules/playwright/cli.js install firefox
```

Если Playwright сообщает об отсутствующих системных библиотеках, использовать штатную подготовку поддерживаемого хоста. Не отключать ограничения среды ради статуса PASS. В исторической Work-среде Firefox скачан, но запуск MCP блокировался политикой Unix-сокетов (`EPERM`). Принятый Mac-запуск завершил три UI-сценария PASS; исходные записи находятся в `evidence/mac/replay-mac-001/evidence/`.

## Приложение и существующие тесты

```bash
cd app
PYTHONPATH=src ../.venv/bin/python -m uvicorn bublik.main:create_app --factory --host 127.0.0.1 --port 8003
```

Открыть `http://127.0.0.1:8003/ui`. API: `/health`, `POST /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}/status`.

В другом терминале из `day-03/app`:

```bash
PYTHONPATH=src ../.venv/bin/python -m pytest -q
```

## Первый запуск новых тестов и replay

Исходный prompt: `prompts/code-testing.txt`. Выбор и точная команда исторического первого запуска: `evidence/code/selection.json`, `evidence/code/first-run/result.json`. Сам лог: `stdout.txt`, `stderr.txt`, `junit.xml` в том же каталоге. Скрипт запрещает перезапись каталога попытки.

Для повторения выбрать три имени из `selection.json` и использовать новый каталог:

```bash
.venv/bin/python scripts/run_code_tests.py --app app --run-dir /tmp/bublik-d3-replay-001 tests/test_d3_dependencies.py tests/test_d3_service_failures.py tests/test_d3_memory_concurrency.py
```

Replay проверяет сохранённую генерацию; он не становится новым историческим first-run. Для новой агентной генерации см. AGENT_WORKFLOW_RU.md.

## Реальный Playwright MCP

Клиент использует настоящий npm-пакет `@playwright/mcp`, транспорт JSON-RPC stdio. Он не вызывает Playwright API напрямую. Приложение и MCP запускаются дочерними процессами одной команды, что совместимо со средой с раздельными loopback namespace. Сначала остановить отдельно запущенный uvicorn на порту 8003.

```bash
.venv/bin/python scripts/mcp_console.py --mcp-cli browser/node_modules/@playwright/mcp/cli.js --app app --evidence replay-001/evidence/mcp
```

В stdin клиента передавать JSON, по одному вызову после проверки предыдущего ответа:

```json
{"tool":"initialize","record":"evidence/initialize.json"}
{"tool":"tools/list","record":"evidence/tools.json"}
{"tool":"browser_navigate","arguments":{"url":"http://127.0.0.1:8003/ui"},"record":"evidence/UI-01/01-navigate.json"}
```

`record` и относительные имена screenshots разрешаются от корня попытки (`replay-001` в примере). Использовать актуальные schemas из `tools/list` и refs/селекторы из фактического snapshot, не угадывать refs. После каждого шага сценария вызвать `browser_take_screenshot` с `type=png`, `scale=css`, `filename=evidence/screenshots/UI-01/step-01.png`; сохранить отдельный MCP record. Команда `{"tool":"quit"}` завершает клиент и оба сервера. Нельзя перезаписывать исторические evidence текущей поставки.

Три сценария версии 1.0.0 находятся в `scenarios/` и сохранены без изменений. Исторический Work preflight завершился BLOCKED/EPERM; принятый Mac smoke выполнил UI-01/02/03 PASS. Его 31 MCP-запись и 9 PNG шагов сохранены в `evidence/mac/replay-mac-001/evidence/`; дополнительный оригинальный preflight.png сохранён отдельно от девяти шагов. r2 собирает эти результаты offline, новых выполнений не было.

## Проверка поставки

```bash
.venv/bin/python scripts/verify_candidate.py
```

Команда проверяет manifest и соответствие сохранённой генерации текущим файлам. Для Git-проверки выполнить её из исходного checkout с `day-03/`; архив содержит только `day-03/`, а не весь репозиторий. Для переноса распаковать его в чистый checkout утверждённого baseline. Commit, push, PR и merge требуют следующего решения Control.

## Проверка исходных manifests в r2

[Проверка входов](evidence/assembly/input-integrity.json) фиксирует SHA обоих ZIP и исходный r1 manifest 93/93. Оригинальные r1 документы/manifest находятся в `evidence/history/r1/`; source-path mapping позволяет проверить все исходные байты после обновления общих документов. Оригинальный Mac SHA256SUMS покрывает девять PNG шагов:

```bash
cd evidence/mac
shasum -a 256 -c replay-mac-001/evidence/SHA256SUMS
```

Финальный SHA256_MANIFEST.json покрывает все файлы r2, кроме самого manifest, включая 31 MCP record, все PNG, исторические r1 documents и исходные manifests. Финальная проверка — целостность артефакта; она не запускает pytest/MCP. `evidence/assembly/link-verification.json` содержит проверку ссылок общего отчёта и Mac report; runtime `.playwright-mcp/*.yml` из исторического tool text не поставлялись, inline browser_snapshot сохранены.

Оригинальный r1 manifest сохранён побайтно как `evidence/history/r1/SHA256_MANIFEST_r1.json`: архивное имя уточнено, чтобы неизменённый r1 verifier не исключал вложенный manifest по basename. Исходный путь → архивный путь указан в input-integrity.json.
