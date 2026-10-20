# Исторический эксперимент Rules v1/v2

Обе генерации действительно выполнены на Mac: Codex CLI 0.163.0, gpt-6.1-sol, medium, runtime R1/R2 и launcher 1.0.2. Промпт не менялся: `control_prompt.txt`, SHA `bae146e7ffb012da48486fc4fc27a879d43ec3c3b8b5c61fd27408768f961b6b`. BASE_SHA `b7f7bc2076c3ffabbeb65a2fb4af467b32d4fe0b`. У каждого запуска собственные репозиторий, CODEX_HOME и новая сессия; один launcher turn/start, без автоматического запуска следующего варианта. Полные нативные config/skills и зависимости совпали после нормализации собственных путей.

| Факт | Rules v1 | Rules v2 |
| --- | --- | --- |
| Внешние acceptance cases, общий E1 | 17/17 PASS | 17/17 PASS |
| pytest проекта | 84 PASS | 81 PASS |
| Compile / import / Ruff lint / format | PASS | PASS |
| Изменённые исходники | routes, schemas, service | routes, schemas, service, errors |
| Новые тестовые файлы | test_status_api, test_status_service | test_status_api, test_status_service |
| Runtime agent_type | architecture_report | architecture_report |
| Runtime task_name | status_architecture | architecture_report |
| Возвращаемый ArchitectureReport | SUCCESS, findings=[] | SUCCESS, findings=[] |
| Реальные tools дочернего агента | 1 read-only exec | 1 read-only exec |
| Семь пропусков return annotations в новых тестах | Нет | **FAIL, сохранён** |
| Ручные исправления исторического кода | Нет | Нет |

Уточнение v2 основано на факте `task_name=status_architecture`: три строки явно требуют `agent_type="architecture_report"` и `task_name="architecture_report"`. Целевое имя во втором запуске соблюдено. Функциональное улучшение не установлено: одинаковый внешний контракт проходит в обеих версиях. Снижение числа pytest cases не является доказательством ухудшения или улучшения: параметризация различается.

API тонкий и использует внедрённый TaskService, DTO запрещает лишние поля. Application зависит от порта и domain, использует immutable replace/save; concrete adapter создаётся только в composition root. В v2 добавлена InvalidTaskStatusError для прямого service-вызова. Существенных архитектурных нарушений не выявлено; статические проверки не доказывают отсутствие всех возможных динамических зависимостей.

Двадцать отсутствующих return annotations в старых baseline-тестах — отдельный найденный долг, не уникальный результат v2. Исторический Ruff игнорировал ANN201 во всех tests. Чистовая копия устраняет и этот долг, и семь новых пропусков; она не является третьей генерацией и не подставляется в историческое сравнение.

Первоначальные external acceptance запуски получили collection exit 4 из-за обхода закрытого lab root; исходные ошибки сохранены приватно. Общий E1 исправил только invocation rootdir/confcutdir, после чего те же 17 cases прошли в обеих версиях. Чистовая проверка использует эти же границы и дополнительно требует уникальные PASSED node IDs.

Фактические исходники обеих генераций: `experiment/v1/source/`, `experiment/v2/source/`, сверяемые `SOURCE-SHA256.json`. Прямое сравнение — `v1-vs-v2-code.diff`; diff каждого варианта относительно baseline лежит рядом с его source. Результаты subprocess сохранены в JSON рядом. В этих публичных производных логах только локальный путь заменён на `<LAB>`; исходные журналы и ZIP сохранены без изменения в отдельном приватном пакете.

Нативные извлечения: `native-evidence-extract.json`, `native-observations.json`; сырой runtime message исключён. Связь parent/child проверена по явному native parent_thread_id. Входное сообщение в генерациях зашифровано runtime — все plaintext-поля повторно не подтверждаются. Gate 2 отдельно подтвердил structured MISSING_REQUIRED_INPUT с 0 native tools и успешный вызов с 1 native tool; принятую диагностику см. `gate2-accepted-evidence.json`.

Наблюдаемые затраты: launcher v1 101.173 s, v2 99.469 s; parent native duration 96.473/94.966 s. Parent input/output tokens — 223130/3554 и 229636/3972; child — 39448/385 и 39653/333. Полные per-thread counters сохранены в native-observations. Cache, случайность модели, один пример на вариант и неизвестные HTTP/SSE retries не позволяют объявлять причинную экономию от изменения Rules. Один turn/start не означает один HTTP-запрос. Все ограничения сохранены в RISK_REGISTER_RU.md.
