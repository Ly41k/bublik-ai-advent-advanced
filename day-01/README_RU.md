# Бублик — Day 1: чистовая основа и учебный эксперимент

Это отдельная чистовая копия Generation 2. Исходные Generation 1/2 и Rules v1/v2 не переписаны. Новый endpoint и бизнес-логика сохранены побайтово. Исправлены 27 return annotations: семь в новых тестах Generation 2 и двадцать ранее скрытых исключением Ruff в baseline-тестах. Удалено исключение ANN201 для tests; добавлены проверки общего gate. Новых модельных запусков нет.

## Статусы

- Foundation Quality Gate: PASS в Linux Work и на Mac Darwin arm64, Python 3.13.3. Mac: `proof/mac-final-2026-10-20/mac-foundation-001.json`.
- Historical Experiment: v1 — 17/17 acceptance, 84 pytest; v2 — 17/17 acceptance, 81 pytest и исторический FAIL по семи return annotations. Это не результаты чистовой копии.
- **Course Minimum: PASS.** Все обязательные требования и реальные скриншоты подтверждены: `course/REQUIREMENTS_RU.md`, `proof/mac-final-2026-10-20/acceptance.json`.
- Advanced Maximum: DEFERRED. Bublik Ready: отдельная оценка, не заявлена.

## Структура пакета

`app/` — запускаемый сервис; `control/` — защищаемые при проверке входы и неизменные 17 внешних cases; `course/` — Rules, промпт, исторические исходники, диффы и отчёты; `proof/` — фактические результаты; `reference-tooling/` — сохранённые исходники offline regression suites; `tooling_regressions.py` — их запуск без модели. Исторический `service.py` внутри reference-tooling нужен только как fixture существования source reference, не как runtime приложения.

## Установка на Mac

Распакуйте ZIP в **новую папку**, вне исходного репозитория и `$BUBLIK_LAB`. Не накладывайте пакет на workspaces v1/v2, CODEX_HOME или старые evidence. См. `MAC_FINAL_RU.md`.

Требуется Python **3.13.3**. Codex для этих проверок не запускается и повторно не устанавливается. В `app/`:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python scripts/run_checks.py --output local-evidence/mac-foundation-001.json
```

Не меняйте lockfiles и версии ради установки. Первый setup требует сети; тесты и gate — нет. Для повторной локальной проверки используйте новое имя отчёта: существующие не перезаписываются. Изоляцию виртуального окружения Mac от Linux Work сохраняйте.

## Запуск сервиса

Из `app/`:

```bash
.venv/bin/python -m uvicorn bublik.main:create_app --factory --host 127.0.0.1 --port 8000
```

Доступны `GET /health`, `POST /tasks`, `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}/status`. Пример создания: `curl http://127.0.0.1:8000/tasks -H 'Content-Type: application/json' --data '{"title":"Learn Rules"}'`. Полученный UUID подставьте в PATCH с телом `{"status":"done"}`. Swagger: <http://127.0.0.1:8000/docs>. Состояние живёт в памяти одного процесса и сбрасывается при перезапуске.

## Что реально проверяет gate

1. Контроль SHA защищённых файлов и инвентаря Python-файлов до запуска.
2. Compile и import приложения.
3. Ruff lint, включая ANN для тестов и новых функций; Ruff format.
4. Полный pytest, включая архитектурные границы и regression tests gate.
5. Все 17 внешних acceptance cases с E1 rootdir/confcutdir вне app/; нужны уникальные PASSED node IDs и exit 0.
6. Offline native trace 102 tests, E1 7 tests, agent contracts 5 tests.
7. Повторный контроль защищённых файлов после выполнения.

Ошибка, пропущенная проверка из-за ненулевого subprocess exit или изменённый защищённый файл не даёт PASS. В отчёте сохраняются stdout/stderr, команды, exit codes, время, ОС/Python и версии библиотек. Точечные положительный и отрицательные тесты Ruff реально выполняются; тесты агрегации с mock subprocess помечены как unit-тесты и не выдаются за запуск инструментов.

Архитектура контролируется существующим AST-тестом статических импортов через обязательный pytest; дублирующего архитектурного валидатора нет. Произвольные динамические импорты он не запрещает. Аннотации проверяются Ruff, второго AST-validator нет.

## Защищённые входы и будущие задачи

`control/protected-inputs.json` фиксирует **эту принятую чистовую версию**. Runner не обновляет его автоматически. Для независимо закреплённого доверенного SHA используйте `--protected-manifest /external/protected-inputs.json --protected-sha256 <approved-sha>`. Совместимый с прежним skill запуск без этих аргументов читает пару manifest/SHA из соседнего control/; сама пара файлов не является независимой границей безопасности.

При следующей согласованной задаче новые допустимые изменения требуют отдельного просмотра diff и явного обновления контрольного снимка. Автоматически принимать изменившийся manifest нельзя. В модельной среде доверенный manifest/SHA должны быть вне разрешённой агенту записи. R1/R2 этой чистовой проверкой не менялись; новая модельная сессия не выполнялась.

Не запускайте CLI из reference-tooling: они сохранены как pinned sources для offline tests; совместимый collector — v2.0.3. Для реального Mac native extraction используйте исходный принятый Gate 2 пакет с его manifest chain. Legacy collector нужен сохранённым тестам как импорт, не как рекомендованный entry point.

Сырые native sessions, приватные evidence ZIP, auth и машинные конфигурации исключены из GitHub-пакета. Публикация не выполнена и требует отдельного согласования.

## Финальная приёмка и публикация

Mac-отчёт совпадает с принятым защищённым манифестом и Work-версиями инструментов: 7 этапов exit 0; 97 pytest; 17 acceptance; tooling 102/7/5; protected before/after PASS. Два PNG терминала проверены визуально, их SHA в proof/mac-final-2026-10-20/screenshots-manifest.json. Оригинальные PNG содержат локальные username/hostname/path, поэтому сохранены в отдельном приватном evidence ZIP для предоставления преподавателю, не внутри GitHub-пакета. Изображения не редактировались.

Актуальные итог и статусы: course/DAY_1_FINAL_RU.md. Предыдущие статусы BLOCKED сохранены как исторические в course/history/ и proof/history/. Инструкция подготовки Git-публикации: PUBLISH_RU.md. Никакой публикации из этой проверки не выполнялось. Неизвестные retries и ограничения доказательства изоляции сохраняются в risk register, без новых исследований или генераций.
