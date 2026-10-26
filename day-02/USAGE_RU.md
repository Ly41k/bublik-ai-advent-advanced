# Инструкции и переключение двух профилей

## Состав

| Профиль | Публичный instruction export | Что делает | Что запрещено |
|---|---|---|---|
| Bug Fix Engineer | `profiles/bug_fix_engineer.md`, версия v3 | Reproduce → collection → RED_EXPECTED → minimal fix → тот же GREEN → host Gate; отдельный Discussion для объяснения готового fix | Игнорировать тесты; считать import error ожидаемым RED; менять существующие tests/locks/Rules; выходить за разрешённые два файла |
| Researcher | `profiles/researcher.md`, версия v4 | Самостоятельно читает исходники, проверяет связи, цитаты и SHA; отделяет факты от предложений; возвращает Markdown по явному запросу | Менять приложение/конфигурацию, реализовывать исследуемую будущую функцию, выдавать host checks за свои, выдумывать hashes |

Общие инструкции: `profiles/common.md`. Фактический канал исторического
API — **developerInstructions**, а не заявленная системная роль.
Сборка: `common + "\n" + specific`. SHA всех фактически использованных версий
сверены с десятью настоящими `thread/start` из существующей истории.
В [profiles/versions.json](profiles/versions.json) перечислены версии и hashes.

Это две роли, даже при нескольких версиях инструкций. Discussion — режим Bug Fix
Engineer для explanation-only запроса, а не третий профиль. Старые версии в
`profiles/versions/` — исторические snapshots. Researcher v5 в
`profiles/candidates/` — только существующий offline candidate; он не выдаётся
за установленную или проверенную реальным ответом версию. По окончательному решению v5 **DEFERRED / NOT_RUN**, Turn 11 **CANCELLED**. Реальный результат v4 **Technical PASS / User ACCEPTED**; это зафиксировано отдельным decision record.

## Выбор профиля

Существующий parser `profiles.py` принимает:

```text
/tester <описание бага или запрос объяснения>
/researcher <вопрос по исходникам>
<следующий запрос без команды использует выбранный профиль>
```

Команда без вопроса выбирает профиль без модельного turn. Неизвестная команда,
пустой запрос или отсутствие выбранного профиля возвращают ошибку; роль не
угадывается. Чистые `parse()` и `instructions()` работают без Codex и сети:

```bash
python3 -B -c 'from profiles import parse, instructions; print(parse("/tester", None)); print(parse("/researcher Вопрос", "tester")); print(len(instructions("researcher")))'
```

Эта offline-проверка не является выполнением реального Research. Его evidence
уже существует и вынесено отдельно. Прежняя runtime-интеграция зависела от
приватных pinned host paths, receipts и admission. Live transport/launchers
не включены в публичный package. Поэтому это **не автономный live runner** и
публичный export инструкций не означает новую установку профиля в Codex.
Новых native запусков по этой инструкции не требуется и не разрешается.

`reference/*.py.txt` — неизменённые исходники исторических console implementations
для code review. Они сохранены как текст и не являются командами запуска.
Исходники `core.py`, `profiles.py`, `history.py`, `documents.py` — существующие
pure/controller компоненты, без transport. Новая архитектура не добавлялась.

## Формат ответа

Bug Fix: «что нашёл → причина → что исправил → что проверил → статус» с префиксом
`Bug Fix Engineer:`. Research: файлы, связи, результаты, выводы, источники и
ограничения с префиксом `Researcher:`. Envelope содержит `profile_id`, `status`,
`answer`, `sources`, `limitations`, `document`. Ошибка выполнения сохраняется как
FAIL/BLOCKED, а не заменяется заявлением PASS. Markdown Research передаётся
хосту в `document`; запись выполняется только ограниченным writer хоста.

## История и restart

`history.py` сохраняет один логический разговор с hash chain, выбранным профилем
и полными сообщениями. Native thread может быть новым для каждого turn;
это не обещание одного вечного native thread. Консоль передавала весь видимый
диалог с признаком history-is-data и блокировала превышение лимита, не обрезая его.

Существующее evidence показывает смену tester → researcher между Turns 7 и 8
и новый процесс консоли перед Turn 9 с восстановленным researcher. Это restart
консоли и replay сообщений, а не доказательство persistence in-memory Task Service
или глобальной SQLite Codex. Приватная история в этом пакете отсутствует.

## Проверка целостности

Из корня всего распакованного candidate:

```bash
python3 -B day-02/verify_delivery.py
```

Проверка только читает candidate и manifest, не импортирует app, native runner,
Codex или history. Она не запускает модель и не создаёт журналы.

Researcher v4 не требует нового испытания; принятие пользователя относится к сохранённому Turn 10. Исторические ответы с прежним PENDING/NOT_GIVEN остаются неизменными.

Исторический app Gate: Python 3.13.3, 110 pytest + 17 acceptance и 13-case regression
подтверждены сохранёнными Mac logs. Установку зависимостей, новый полный Mac Gate
и live execution эта offline delivery task не выполняет. Не считать сохранённый
PASS результатом нового запуска.
