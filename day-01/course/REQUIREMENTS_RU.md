# Матрица полного покрытия Day 1

Основание: пункты оригинального задания Rules и полный перечень обязательной приёмки, приведённый пользователем. Статус PASS означает наличие названного артефакта и наблюдавшейся проверки; описания процедуры недостаточно. Все строки подтверждены, включая полученные и визуально проверенные реальные скриншоты Mac.

| № | Требование | Статус | Артефакт / фактическое подтверждение |
| --- | --- | --- | --- |
| 1 | Rules v2 | PASS | app/AGENTS.md, course/rules-v2.AGENTS.md; SHA сохранён, точная вставка v1→v2 проверена |
| 2 | Стек | PASS | AGENTS.md: Stack and commands; actual tool_versions в proof/foundation-quality-work.json |
| 3 | Архитектура и папки | PASS | AGENTS.md: Structure and architecture; source/ обеих генераций; tests/test_architecture.py реально выполнен в pytest |
| 4 | Naming conventions и паттерны | PASS | AGENTS.md: Naming and patterns; реальные typed DTO/Protocol/DI/immutable Task; clean Ruff ANN PASS |
| 5 | Глобальные и локальные Rules | PASS | course/GLOBAL_AGENTS_V1.md и app/AGENTS.md; native instructionSources в course/native-evidence-extract.json; Gate 2 accepted evidence |
| 6 | Реальные subagents | PASS | native spawn_agent с agent_type architecture_report, child link, 1 tool и контракт результата; native-evidence-extract.json |
| 7 | Реальные skills | PASS | app/.agents/skills/quality-gate/SKILL.md; принятый Gate 2, реальные generation native read+runner, исторические logs |
| 8 | 3–5 хороших примеров из проекта | PASS | AGENTS.md: Five examples from the accepted baseline — 5 путей/символов с реальным кодом |
| 9 | 3–5 антипаттернов | PASS | AGENTS.md: Five antipatterns and alternatives — 5 запретов и альтернатив |
| 10 | Шаблон типичного файла | PASS | AGENTS.md: Typical application module — импорты, типы, класс и public function |
| 11 | Реальная новая задача endpoint | PASS | PATCH /tasks/{task_id}/status в experiment/v1,v2/source; external-acceptance-e1.json — 17/17 у обеих |
| 12 | Один неизменный промпт | PASS | course/control_prompt.txt; SHA bae146e7…f961b6b совпал в обоих реальных turn/start |
| 13 | Компиляция, линтер, тесты, стиль | PASS | experiment/v1 и v2/*.json: compile/import/Ruff/pytest; 84/81 PASS; общий E1 17/17 |
| 14 | Обоснованное улучшение правил | PASS | rules-v2-change-log.md, rules-v1-to-v2.diff; наблюдение status_architecture и исправленный task_name=architecture_report |
| 15 | Повторная генерация и сравнение | PASS | COMPARISON_RU.md; baseline-to-generated.diff каждого варианта; v1-vs-v2-code.diff; реальные source snapshots |
| 16 | Реальные логи, Git diff, факторы качества | PASS | subprocess JSON, native extracts и SHA приватных оригиналов; COMPARISON_RU.md: cache, stochasticity, настройки, ограничения |
| 17 | Реальные скриншоты | PASS | proof/mac-final-2026-10-20/acceptance.json, screenshots-manifest.json; два оригинальных PNG в отдельном приватном архиве, визуально проверены |
| 18 | Чистовая копия отдельно от истории | PASS | app/; proof/clean-origin.json; 27 annotations, из них 7 новых; бизнес-исходники неизменны |
| 19 | Автоматические annotations / positive + negative | PASS | Ruff ANN без exemptions; tests/test_foundation_gate.py; real Ruff; proof/historical-v2-annotation-negative.json |
| 20 | Общий fail-closed Quality Gate | PASS | scripts/run_checks.py; 7 mandatory subprocesses; pre/post integrity; 7 отрицательных aggregation cases, real checks в proof/foundation-quality-work.json |
| 21 | Архитектурные ограничения автоматически | PASS | Обязательный pytest включает tests/test_architecture.py и negative FastAPI-in-domain fixture |
| 22 | E1, native trace, контракты/fail-fast закреплены | PASS | reference-tooling; 102 + 7 + 5 regression tests; native-collector-verification.json; реальные принятые Gate 2 0/1 tools |
| 23 | Исторические inputs/evidence неизменны | PASS | proof/history-integrity.json: 253 файлов, 6 ZIP, git tracked diff exit 0 |
| 24 | README и воспроизводимый запуск | PASS | README_RU.md, app/README.md, MAC_FINAL_RU.md; фактический Work Python 3.13.3, hashed locks сохранены |
| 25 | Безопасный GitHub-пакет отдельно от приватного | PASS | Отдельный ZIP с DELIVERY-SHA256.json и verify_delivery.py; raw native sessions/auth исключены; публикация не выполнялась |

**Course Minimum: PASS — все обязательные строки подтверждены.** Foundation Quality Gate: PASS в Linux Work и на Mac Darwin arm64 / Python 3.13.3. Финальная приёмка: proof/mac-final-2026-10-20/acceptance.json. Исторические генерации не исправлены: у Generation 2 сохранён FAIL по семи аннотациям. Предыдущая матрица со скриншотным блокером сохранена в course/history/. Публикация только подготовлена, push/merge не выполнялись.
