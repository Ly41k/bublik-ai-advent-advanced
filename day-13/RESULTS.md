# Day 13 · G1 Offline Results

**Gate** — G1_OFFLINE_IMPLEMENTATION_READY_FOR_CONTROL_REVIEW  
**Вариант** — A, Course Minimum  
**Источник evidence** — синтетические fixtures, FastAPI TestClient, детерминированный Mock Provider и подставные клиенты при проверке формы SDK-вызова  
**Live OpenAI** — NOT_RUN, 0 запросов, фактические usage и стоимость UNKNOWN  
**Mac Owner / Control Review / GitHub** — NOT_RUN  

## Среда и повтор

Linux x86_64, CPython 3.13.17, FastAPI 0.121.0, Starlette 0.49.3, anyio 4.16.0, HTTPX 0.28.1, OpenAI SDK 2.54.0, pytest 8.4.2, Uvicorn 0.38.0.

~~~sh
unset OPENAI_API_KEY
export GATEWAY_PROVIDER=mock LIVE_ENABLED=false
python -m pytest -q
python -m tests.smoke
~~~

**69/69 PASS**. Из них **24/24** по утверждённой матрице. В матрице зафиксировано **0 FAIL, 0 MISSED и 0 ложных срабатываний**. Starlette TestClient выдал одно предупреждение о deprecated alias anyio BlockingPortal.

## Утверждённая матрица

Статусы и счётчики получены из фактического pytest-прогона. Счётчик провайдера для T17 относится только к шестой попытке. В T24 категория API_KEY относится к причине блока, а критерий сценария относится к учёту стоимости.

| ID | Стадия | Режим | Критерий | Ожидалось | Фактически | Категории аудита | Вызовы провайдера | Итог |
|---|---|---|---|---|---|---|---:|---|
| T01 | input | block | zero_provider_call | 403 | 403 | API_KEY | 0 | PASS |
| T02 | input | block | zero_provider_call | 403 | 403 | API_KEY | 0 | PASS |
| T03 | input | block | zero_provider_call | 403 | 403 | GITHUB_TOKEN | 0 | PASS |
| T04 | input | block | zero_provider_call | 403 | 403 | AWS_KEY | 0 | PASS |
| T05 | input | block | zero_provider_call | 403 | 403 | EMAIL | 0 | PASS |
| T06 | input | block | zero_provider_call | 403 | 403 | PHONE | 0 | PASS |
| T07 | input | block | zero_provider_call | 403 | 403 | CARD | 0 | PASS |
| T08 | input | block | negative_luhn | 200 | 200 | — | 1 | PASS |
| T09 | input | block | one_level_base64 | 403 | 403 | API_KEY | 0 | PASS |
| T10 | input | block | fragment_join | 403 | 403 | API_KEY | 0 | PASS |
| T11 | input | block | clean_passthrough | 200 | 200 | — | 1 | PASS |
| T12 | input | mask | mask_forwards_redacted_only | 200 | 200 | API_KEY | 1 | PASS |
| T13 | output | block | no_raw_output | 403 | 403 | API_KEY | 1 | PASS |
| T14 | output | block | no_raw_output | 403 | 403 | SYSTEM_PROMPT | 1 | PASS |
| T15 | output | block | no_url_fetch | 403 | 403 | SUSPICIOUS_URL | 1 | PASS |
| T16 | output | block | never_execute | 403 | 403 | DANGEROUS_COMMAND | 1 | PASS |
| T17 | rate | block | zero_provider_call | 429 | 429 | RATE_LIMIT | 0 | PASS |
| T18 | provider | block | no_error_leak | 502 | 502 | PROVIDER_ERROR | 1 | PASS |
| T19 | audit | block | no_secret_bytes | PASS | 5×403, audit scan PASS | — | 0 | PASS |
| T20 | cost | block | correct_token_cost | PASS | 200 | — | 1 | PASS |
| T21 | output | block | no_false_positive_benign_command | 200 | 200 | — | 1 | PASS |
| T22 | input | mask | both_redacted | 200 | 200 | EMAIL, PHONE | 1 | PASS |
| T23 | input | block | negative_plain_digits | 200 | 200 | — | 1 | PASS |
| T24 | cost | block | blocked_output_still_billed | PASS | 403 | API_KEY | 1 | PASS |

## Что подтверждает evidence

- evidence/smoke.json содержит фактические статусы четырёх HTTP-проверок. Во всех сценариях используется локальный ASGI transport. Перехватчик DNS и socket.connect/connect_ex/sendto действует в каждом тесте и в smoke. Зафиксировано 0 попыток.
- evidence/audit-mock.jsonl содержит четыре отобранные строки из шести попыток smoke. В выдержку вошли чистый ответ, входная блокировка, маскирование и rate limit.
- evidence/audit-blocked-output.jsonl содержит строку T24 из того же pytest-прогона. HTTP 403 на выходе сохраняет оценку $0.00001955 для 100 входных, включая 5 кэшированных, и 20 выходных токенов. Формула по тарифам G0 версии gpt-6-luna-standard-text-2026-11-04 — (95 × $0.10 + 5 × $0.01 + 20 × $0.50) / 1 000 000. Это синтетическая оценка.
- В T12 провайдер получил только текст с [REDACTED_API_KEY], а в T22 с [REDACTED_EMAIL] и [REDACTED_PHONE]. В T09 и T10 заблокированы соответственно закодированный и разбитый ключи. Отдельные тесты проверяют маскирование всей Base64-последовательности и всей цепочки фрагментов.
- Для T08, T11, T21 и T23 подтверждён пропуск отрицательных примеров. Отдельно пройдены проверки fail closed при сбое аудита, при остаточном секрете после маскирования, на граничных размерах, при конкурентных запросах и при отсутствии usage.
- Каждая сессия проверок сканирует синтетические значения в JSONL и захваченных логах. T19 также проверяет отсутствие полных промптов в JSONL. Ответы 403, 429 и 502 проверены на отсутствие исходных защищённых значений. Выходные признаки из T13–T16 не попали в HTTP-ответ. В ZIP включены fixtures, которые собирают синтетические тестовые значения во время запуска.
- Тариф, идентификатор модели и настройки запроса взяты из замороженного G0. Тест адаптера проверяет аргументы SDK и разбор подставного ответа. Совместимость с реальным аккаунтом, тарификация и доступность модели требуют отдельного live-пилота.

## Границы измерения

Luhn может совпасть с обычным числовым идентификатором. Контекстное распознавание телефонов может ошибиться на идентификаторе с телефонной меткой. Неразмеченные локальные телефоны, международные адреса со сложным синтаксисом, скрытая пунктуация в ключах, нестандартные формы URL и перефразирование системных инструкций могут пройти. Вложенный Base64 и длинные последовательности вне заданной границы специально пропускаются и проверены отрицательными тестами. Политика пустого списка внешних URL намеренно блокирует и обычные ссылки.

## G3 · Офлайн-проверка владельца на macOS

4 ноября 2026 года. Python 3.13.3, установленный OpenAI SDK 2.54.0. На Mock Provider прошли **69/69 тестов**, включая **24/24 сценария** матрицы выше. Получено одно предупреждение Starlette/AnyIO об устаревшем интерфейсе.

## G4 · Пилот OpenAI API на macOS

4 ноября 2026 года. Источник — очищенная сводка терминала владельца, принятая Control. Перед пилотом /health показал status=ok, live_enabled=true, model=gpt-6-luna и policy_version=d13-guard-r1. Проверки доступности API и видимости модели вернули HTTP 200.

| Сценарий | HTTP | Решение шлюза | Вызов модели | Входные токены | Кэшированные входные | Выходные токены | Локальная оценка USD |
|---|---:|---|---|---:|---:|---:|---:|
| Чистый запрос | 200 | allow | OPENAI_API | 32 | 0 | 6 | $0.00000620 |
| Блокировка синтетического ключа | 403 | input block · API_KEY | Не отправлен, по ответу шлюза | — | — | — | — |
| Маскирование синтетического ключа | 200 | mask · API_KEY | OPENAI_API | 45 | 0 | 29 | $0.00001900 |
| **Итого** | | | **2 вызова** | **77** | **0** | **35** | **$0.00002520** |

В ответе на маскированный запрос владелец увидел маркер [REDACTED_API_KEY]. Локальная проверка аудита владельцем — PASS. В журнале 3 записи, по одной для выходного allow с HTTP 200, входного block с HTTP 403 и выходного mask с HTTP 200. В сводке отмечены 2 записи с фактическим обращением к модели и единственная метка origin OPENAI_API. Локальная проверка владельца не обнаружила исходный синтетический секрет в журнале.

Публичные файлы evidence/ относятся к синтетическому G1. Сводка G4 приведена со слов владельца. Исходный журнал владельца и фактический счёт OpenAI независимо не сверялись. Пилот проверяет перечисленные сценарии входной защиты.
