# BUBLIK-D3-MAC-SMOKE-001 — реальный UI smoke

После выполнения smoke SHA256SUMS проверен: 9/9 OK. Дополнительная проверка рабочего каталога `git status --short` вернула exit 128: `fatal: not a git repository (or any of the parent directories): .git`. Вероятный компонент — метаданные Git рабочего каталога. Это не ошибка сценариев UI; их наблюдаемый PASS сохраняется. После записи ошибки дальнейшие действия остановлены.

UI-01: **PASS**. UI-02: **PASS**. UI-03: **PASS**.

Сценарии scenarios/UI-01.md, UI-02.md, UI-03.md версии 1.0.0 прочитаны и выполнены строго по очереди. Реальный сервер playwright-day3, URL http://127.0.0.1:8003/ui. Read-only browser_evaluate подтвердил Firefox/156.0 на Mac.

Выполнен 31 настоящий MCP-вызов. Полные аргументы и ответы сохранены в mcp-calls/001.json … 031.json. browser_snapshot подтверждает каждый шаг. browser_evaluate использован только для чтения userAgent и DOM task ID/состояния. Все действия пользователя выполнены browser_type/browser_click через MCP.

| Сценарий / шаг | Assertion (PASS) | MCP записи | PNG |
|---|---|---|---|
| UI-01 / 1 | Task title и Create присутствуют; список Tasks пуст. | [mcp-calls/001.json](mcp-calls/001.json), [mcp-calls/002.json](mcp-calls/002.json), [mcp-calls/003.json](mcp-calls/003.json), [mcp-calls/004.json](mcp-calls/004.json) | [PNG](screenshots/UI-01/step-01.png) |
| UI-01 / 2 | Значение Task title равно UI-01 Bublik task. | [mcp-calls/005.json](mcp-calls/005.json), [mcp-calls/006.json](mcp-calls/006.json), [mcp-calls/007.json](mcp-calls/007.json) | [PNG](screenshots/UI-01/step-02.png) |
| UI-01 / 3 | Ровно одна listitem, title UI-01 Bublik task, status todo. | [mcp-calls/008.json](mcp-calls/008.json), [mcp-calls/009.json](mcp-calls/009.json), [mcp-calls/010.json](mcp-calls/010.json) | [PNG](screenshots/UI-01/step-03.png) |
| UI-02 / 1 | Отображаемый список Tasks пуст. | [mcp-calls/011.json](mcp-calls/011.json), [mcp-calls/012.json](mcp-calls/012.json), [mcp-calls/013.json](mcp-calls/013.json) | [PNG](screenshots/UI-02/step-01.png) |
| UI-02 / 2 | Значение Task title равно UI-02 Bublik task. | [mcp-calls/014.json](mcp-calls/014.json), [mcp-calls/015.json](mcp-calls/015.json), [mcp-calls/016.json](mcp-calls/016.json) | [PNG](screenshots/UI-02/step-02.png) |
| UI-02 / 3 | Одна задача UI-02 Bublik task, status todo; task ID f2bae8cd-f73f-40b7-af0a-da1b2cdca882. | [mcp-calls/017.json](mcp-calls/017.json), [mcp-calls/018.json](mcp-calls/018.json), [mcp-calls/019.json](mcp-calls/019.json), [mcp-calls/020.json](mcp-calls/020.json) | [PNG](screenshots/UI-02/step-03.png) |
| UI-02 / 4 | Та же задача и ID f2bae8cd-f73f-40b7-af0a-da1b2cdca882; title сохранён, status done, Mark done disabled=true. | [mcp-calls/021.json](mcp-calls/021.json), [mcp-calls/022.json](mcp-calls/022.json), [mcp-calls/023.json](mcp-calls/023.json), [mcp-calls/024.json](mcp-calls/024.json) | [PNG](screenshots/UI-02/step-04.png) |
| UI-03 / 1 | Пустое поле Task title и ноль строк Tasks. | [mcp-calls/025.json](mcp-calls/025.json), [mcp-calls/026.json](mcp-calls/026.json), [mcp-calls/027.json](mcp-calls/027.json) | [PNG](screenshots/UI-03/step-01.png) |
| UI-03 / 2 | Alert: Task title must contain 1–200 characters.; ноль строк Tasks; POST /tasks => [422] Unprocessable Content. | [mcp-calls/028.json](mcp-calls/028.json), [mcp-calls/029.json](mcp-calls/029.json), [mcp-calls/030.json](mcp-calls/030.json), [mcp-calls/031.json](mcp-calls/031.json) | [PNG](screenshots/UI-03/step-02.png) |

Создано **9 новых настоящих PNG**, каждый 1280×720, RGBA. Реальный browser_take_screenshot использовал type=png и scale=css. file распознал все девять PNG; shasum прочитал все файлы, команды завершились кодом 0. SHA256 приведены в SHA256SUMS и smoke-results.json. Совпадение хеша пустых страниц UI-01/step-01 и UI-03/step-01 соответствует одинаковому состоянию; это два отдельных вызова screenshot (004 и 027).

Ошибок MCP или несоответствий assertions не обнаружено. Наблюдавшийся POST /tasks → 422 Unprocessable Content — ожидаемый результат UI-03, компонент: серверная валидация /tasks; UI показывает точный текст ошибки. Отсутствие создания проверено в границах сценария: ноль строк UI + HTTP 422; API списка не вызывался.

Приложение, тесты и исходные сценарии не изменялись. Preflight и исторические evidence не перезаписывались. pytest не повторялся; предыдущий 11/11 PASS сообщён пользователем и не является проверкой этого запуска. Commit/push/PR/merge не выполнялись. Дополнительная разработка не выполнялась.

