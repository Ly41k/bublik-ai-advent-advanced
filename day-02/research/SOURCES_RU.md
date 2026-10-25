# Проверенные источники Research

Сверены существующие source bytes; новых чтений моделью и новых turns не было.

Python: SHA и цитата внутри соответствующего AST symbol. Markdown: SHA, существующий symbol text и точная цитата, без заявления AST.

| Turn | Файл / символ | Строки символа | Проверка |
|---|---|---|---|
| 3 | [src/bublik/infrastructure/memory_repository.py](../app/src/bublik/infrastructure/memory_repository.py) — `InMemoryTaskRepository.__init__` | 12–14 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/application/service.py](../app/src/bublik/application/service.py) — `TaskService.__init__` | 14–15 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/application/repository.py](../app/src/bublik/application/repository.py) — `TaskRepository` | 9–18 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/main.py](../app/src/bublik/main.py) — `create_app` | 10–15 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/api/dependencies.py](../app/src/bublik/api/dependencies.py) — `get_task_service` | 8–13 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [tests/test_api.py](../app/tests/test_api.py) — `test_application_instances_do_not_share_tasks` | 65–68 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/api/routes.py](../app/src/bublik/api/routes.py) — `get_task` | 47–54 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [src/bublik/domain/task.py](../app/src/bublik/domain/task.py) — `Task.__post_init__` | 25–34 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 3 | [docs/BASELINE_CODE_EXAMPLES.md](../app/docs/BASELINE_CODE_EXAMPLES.md) — `TaskRepository` | 1–67 | SHA_AND_DOCUMENT_QUOTE_PASS_NOT_AST |
| 10 | [src/bublik/domain/task.py](../app/src/bublik/domain/task.py) — `Task.__post_init__` | 25–34 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 10 | [src/bublik/main.py](../app/src/bublik/main.py) — `create_app` | 10–15 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 10 | [src/bublik/application/service.py](../app/src/bublik/application/service.py) — `TaskService.__init__` | 14–15 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 10 | [src/bublik/application/service.py](../app/src/bublik/application/service.py) — `TaskService.update_task_status` | 23–32 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 10 | [src/bublik/application/repository.py](../app/src/bublik/application/repository.py) — `TaskRepository` | 9–18 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |
| 10 | [src/bublik/infrastructure/memory_repository.py](../app/src/bublik/infrastructure/memory_repository.py) — `InMemoryTaskRepository` | 9–24 | SHA_AND_SYMBOL_OWNED_QUOTE_PASS |

Полные цитаты и SHA: [verified-sources.json](verified-sources.json).
Original Markdown Turn 3 до sanitization побайтно совпал с `document` исходного результата. Private history markers заменены явным placeholder, остальные research claims не переписаны.
Turn 10: Markdown — сохранённый answer, а не новый документ от модели; сам ответ сообщает document=null.
Упоминание SQLite — историческое предложение в исследовании. Эта сборка не исследует и не реализует SQLite.
