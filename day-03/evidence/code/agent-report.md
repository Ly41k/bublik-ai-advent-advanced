# Gate 2 — CodeTestingReportAgent

**PASS: первый запуск 11/11, exit code 0.**

Самостоятельно выбраны и покрыты три модуля:

| Модуль | Пробел | Новый файл | Cases |
|---|---|---|---:|
| `bublik.api.dependencies` | Некорректная wiring-конфигурация resolver, HTTP 500 | `tests/test_d3_dependencies.py` | 5 |
| `bublik.application.service` | Ошибки чтения/записи repository, порядок валидации | `tests/test_d3_service_failures.py` | 4 |
| `bublik.infrastructure.memory_repository` | Параллельные операции, независимость task identities | `tests/test_d3_memory_concurrency.py` | 2 |

Команда первого запуска (из day-03):

```bash
python scripts/run_code_tests.py --app app --run-dir evidence/code/first-run tests/test_d3_dependencies.py tests/test_d3_service_failures.py tests/test_d3_memory_concurrency.py
```

Реальный interpreter записан в `first-run/result.json`. До первого запуска новые тесты не импортировались, не исполнялись и не проходили pytest collect. После первого запуска тесты не менялись и повторно этим агентом не запускались. Снимки генерации, stdout, stderr, JUnit и exit code сохранены в `first-run/`.

Production SHA до анализа, перед запуском и после запуска совпадают. Старые тесты не менялись. Сравнение зафиксировано в `agent-report.json`. Конечная параллельная нагрузка не доказывает отсутствие всех возможных гонок.

Это результат Gate 2, а не утверждение PASS всего Day 3. UI вне контракта агента.
