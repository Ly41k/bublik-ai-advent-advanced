# Неподтверждённые критерии и отложенная работа

Общий статус Day 2: **PARTIAL / BLOCKED**. Подготовка delivery сама по себе
не закрывает Course Minimum.

| Критерий | Состояние | Почему не PASS |
|---|---|---|
| Чистый успешный Bug Fix с первого original запуска | NOT_DEMONSTRATED | Attempts 1 и 2 FAIL; independent saved-patch PASS подтверждает patch, но не меняет originals |
| Достаточность восстановленного рабочего результата для буквального задания | CONTROL/TEACHER_DECISION_REQUIRED | Итерации разрешены заданием, решение принимающего ревьюера в этой задаче не дано |
| Оригинальный Turn 10 admission receipt в просмотренном export | MISSING_EXPORT | Известен hash и authorization event, но сам receipt отсутствует; не создаётся заново |
| Проверка именно Mac checkout/index пользователя | NOT_CHECKED | Staging выполнен в отдельном Work checkout от подтверждённого main; это не аудит Mac |
| Полный независимый replay-аудит только по публичному candidate | LIMITED | Приватные полные журналы намеренно исключены; публичны проверенные metadata projections и source hashes |
| Оригинальные screenshots в публичной поставке | EXCLUDED | Содержат private machine paths/history; предоставлены sanitized logs и реестр original SHA |
| Новый самостоятельный live runner из public package | NOT_PROVIDED | Приватные machine-bound launchers/receipts исключены; native gate отложен |
| Финальная приёмка и разрешение публикации | PENDING_CONTROL_REVIEW | Эта задача заканчивается candidate, а не созданием PR |

Закрыто окончательным решением пользователя: **Researcher v4 — Technical PASS / User ACCEPTED**. Историческая editorial PARTIAL не переписывается. Researcher v5 — **DEFERRED / NOT_RUN**, дополнительное испытание не требуется. **Turn 11 CANCELLED**. Эти пункты больше не числятся обязательными незавершёнными испытаниями.

Исторические technical PASS для Research и switch/history/restart не отменяются.
Стиль Researcher v3 остаётся NOT_ACCEPTED. SQLite, ACL, утраченное historical
evidence и native security-gate — **DEFERRED**; ACL/SQLite диагностика не возобновляется, восстановление потерянных данных окончательно прекращено. Receipt Turn 10 остаётся MISSING. Это не перенос требований в молчаливый PASS.

Третий профиль — необязательное усиление, **DEFERRED**. Day 3 не начат.
Для устранения открытых пунктов не назначаются автоматически новые turns:
текущий бюджет 10/11, новых модельных вызовов 0.
