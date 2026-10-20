# Подготовленный GitHub-пакет — порядок публикации

Репозиторий: <https://github.com/Ly41k/bublik-ai-advent-advanced>. Пакет готов; команды commit/push/PR ниже сейчас **не выполнялись**. Выполнять публикацию только после отдельного согласования. Generation 1/2 и baseline tags не переписывать.

## Что публиковать

Только содержимое `bublik-day1-course-minimum-github.zip`: чистовой app/, control/, сохранённые offline regression sources, учебные Rules и экспериментальные source snapshots, diff и безопасные отчёты. Приватный ZIP, общую внешнюю обёртку с приватным ZIP, исходные native JSONL, CODEX_HOME и auth не копировать в репозиторий. Оригинальные скриншоты доступны преподавателю отдельно в приватном evidence-пакете; их SHA и визуальная приёмка уже есть в публичном отчёте.

## Локальная проверка пакета

Распакуйте публичный ZIP в новую папку и перейдите в `bublik-day1-course-minimum`:

```bash
python3 -B verify_delivery.py
```

Ожидается status PASS, scope delivery_integrity_only, codex_invocations 0. Это проверка файлов, не повторная генерация и не новый запуск приложения. Если нужен повтор Quality Gate, используйте README и новое имя отчёта; проведённая Mac-приёмка уже приложена.

## Подготовка к публикации после разрешения

В существующем репозитории создайте отдельную ветку. Не используйте reset/clean и не удаляйте лабораторию.

```bash
git status --short --untracked-files=all
git switch -c feat/day-01-course-minimum
```

Скопируйте **только публичную распакованную папку** как `day-01/` внутри репозитория. Это оставляет исторический baseline и Gate 1/2/3 на их прежних путях. Если day-01/ уже существует, остановитесь и сначала сравните её содержимое; не накладывайте копию вслепую.

```bash
test ! -e day-01
```

Убедившись, что проверка выше успешна, выполните копирование в Finder либо через `ditto`, указав фактический путь:

```bash
ditto "/абсолютный/путь/bublik-day1-course-minimum" "day-01"
python3 -B day-01/verify_delivery.py
git status --short --untracked-files=all
```

Основной root README можно дополнить ссылкой `[Day 1 — Rules: Course Minimum PASS](day-01/README_RU.md)` и явно указать, что чистовая рабочая копия находится в day-01/app/. Старые отчёты baseline не переписывать задним числом.

Добавляйте в staging только нужные пути:

```bash
git add -- day-01
# Только если действительно обновлён root README:
git add -- README.md
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
```

Проверьте, что staged нет private-evidence ZIP, screenshots оригиналов, auth.json, .env, .venv, CODEX_HOME, native JSONL и прежних local-evidence. Если любой лишний файл попал в staging — уберите только его через `git restore --staged -- <путь>`, не удаляя файл с диска.

После просмотра staged diff и отдельного разрешения публикации:

```bash
git commit -m "Complete Day 1 Rules course minimum and foundation checks"
git push -u origin feat/day-01-course-minimum
```

Создайте Draft PR в существующем репозитории с описанием из PR_DESCRIPTION_RU.md. Merge отдельно. Новых модельных запусков, переименования baseline tag или перезаписи исторического кода для публикации не требуется.
