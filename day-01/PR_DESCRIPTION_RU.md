# Day 1: Rules v1/v2 и Course Minimum PASS

Добавляет отдельную чистовую копию Bublik Task Service и полный учебный комплект Day 1. Две реальные независимые генерации реализовали PATCH /tasks/{task_id}/status по одному неизменному промпту. Rules v2 уточнили имя делегированной задачи; фактическое имя стало architecture_report. Внешний контракт у обеих генераций равен: 17/17 PASS, функционального улучшения не заявляется.

Чистовая копия отдельно исправляет семь новых и двадцать baseline-пропусков return annotations, удаляет Ruff ANN201 exemption и усиливает общий Quality Gate. Исторические Generation 1/2 не исправлены; FAIL v2 по семи аннотациям сохранён.

Проверки Mac Darwin arm64 / Python 3.13.3: compile/import/Ruff lint+ANN/format PASS; 97 pytest; 17 внешних acceptance cases; 102 native trace, 7 E1 и 5 contract regression tests; protected before/after PASS. Новых Codex/model invocations при финальной проверке — 0. Два настоящих скриншота проверены; оригиналы с локальными путями сохраняются отдельно от публичного пакета, SHA и приёмка приложены.

Ограничения: внутренние HTTP/SSE retries неизвестны, один turn/start не равен одному HTTP-запросу; полной отрицательной проверки всех модельных операций нет. Они ранее приняты и явно сохранены в risk register. Advanced Maximum DEFERRED; Bublik Ready отдельно.
