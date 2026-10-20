# Day 1 — итог подготовки к полной приёмке

## Раздельные статусы

| Область | Статус |
| --- | --- |
| Course Minimum | **BLOCKED: реальные скриншоты ещё не получены** |
| Foundation Quality Gate | **PASS в Linux Work, отдельный CPython 3.13.3** |
| Historical Experiment | Завершён и сохранён; v1/v2 17/17, v2 исторический FAIL по 7 аннотациям не скрыт |
| Advanced Maximum | DEFERRED |
| Bublik Ready | Отдельная оценка, не заявлена |

Отсутствие скриншотов не заменяется ложно-положительным статусом или нарисованной картинкой отчёта. Для закрытия остаются два настоящих снимка по MAC_FINAL_RU.md; новое модельное выполнение не требуется.

## Найденные недостатки и минимальные исправления

1. Ruff пропускал missing return types во всех тестах из-за ANN201 exemption. В чистовой копии исключение удалено, 7 новых и 20 прежних тестовых функций получили `-> None`. Параметры и returns проверяются Ruff ANN. Положительный и два отрицательных real Ruff test проходят; исторические новые тесты v2 проверены новым конфигом и действительно дают 7 ANN201, исходники при этом не изменены.
2. Старый runner проверял только compile/import/Ruff/pytest. Чистовой runner включает external E1 acceptance, pinned offline tooling suites и pre/post protected-input checks. Ошибки не агрегируются в PASS; проверены все семь обязательных ветвей отказа. Существующие результаты не перезаписываются.
3. Старый external pytest invocation обходил закрытый lab root. E1 collection boundaries сохранены; чистовой runner задаёт явные config/rootdir/confcutdir/cache policy. Проверяется ровно 17 уникальных успешно выполненных cases.
4. Native trace исходно не понимал task_name-only и дополнительные native records. Принятый v2.0.3 сохранён без модификации, проверка его manifest PASS, 102 regression tests PASS. Неподтверждённая или неоднозначная корреляция по-прежнему блокируется. Тестовые fixtures не выдаются за новое выполнение Codex.
5. Контракты и fail-fast уже проверены на Mac в Gate 2; их валидаторы и 5 offline regression tests сохранены. Нативные наблюдения 0/1 tools не подменены самоотчётами модели.
6. Недоступность Work была сбоем среды. Среда восстановлена; host Python остаётся 3.12.14. Чистовая проверка реально выполнялась в отдельном установленном Python 3.13.3 с зависимостями по неизменному hashed requirements.lock. Она не объявляется проверкой Mac.

## Фактическое выполнение

`proof/foundation-quality-work.json`: compile/import/Ruff lint+ANN/format/pytest/external acceptance/tooling — все exit 0, protected_before/after PASS. pytest **97 PASS**, внешний frozen файл **17 PASS**. Tooling suites: native trace **102**, E1 **7**, agent contracts **5**. Архитектура проверяется существующим AST-тестом внутри обязательного pytest; отрицательный fixture с FastAPI в domain обнаруживается. Отдельного дублирующего architecture/annotation validator не добавлено.

`proof/clean-origin.json`: бизнес-исходники src/ побайтово равны Generation 2; зависимости, Rules v2, skill и agent config также неизменны. У старых тестов AST после исключения return annotations совпадает. Добавлен только test_foundation_gate.py и укреплён runner/config. Diff: `proof/generation2-to-clean.diff`.

`proof/history-integrity.json`: проверены 253 ранее существовавших файла проекта и 6 исходных ZIP; изменений нет, git tracked diff exit 0. Новые материалы находятся в отдельной day1-foundation, исторические Git snapshots не переписаны.

## Материалы преподавателю и публикация

Матрица покрытия всех перечисленных обязательных требований — REQUIREMENTS_RU.md. Публичный пакет содержит чистовое приложение, Rules, глобальный шаблон, skill/subagent, неизменный промпт, фактические исходники обеих генераций, diff, redacted subprocess logs и производные native extracts с SHA оригиналов. Это не сырые персональные сессии. Приватный архив хранит оригинальные evidence ZIP и подробное ревью отдельно.

Секреты, auth.json, токены, виртуальные окружения, CODEX_HOME, личные журналы и лабораторный Git history не включаются в GitHub-пакет. До публикации его можно проверить локально verify_delivery.py. Push/merge/публикация не выполнялись и остаются отдельным решением.

После добавления реальных скриншотов нужен новый append-only acceptance report; этот файл и прежние evidence не требуется переписывать задним числом. Все остальные обязательные строки матрицы уже подтверждены, общего Course Minimum PASS до закрытия последней строки нет.
