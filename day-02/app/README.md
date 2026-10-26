# Бублик — чистовая версия Day 1

Это исправленная копия Generation 2, а не новый модельный запуск. Бизнес-исходники не изменены. Исторические генерации сохранены отдельно.

Полные установка, запуск, Quality Gate и ограничения: [README_RU.md](../README_RU.md).
Пошаговая проверка на Mac и настоящие скриншоты: [MAC_FINAL_RU.md](../MAC_FINAL_RU.md).

Из этой папки после установки закреплённых зависимостей:

```bash
.venv/bin/python scripts/run_checks.py --output local-evidence/checks-001.json
.venv/bin/python -m uvicorn bublik.main:create_app --factory --host 127.0.0.1 --port 8000
```

Runner требует соседние `control/`, `reference-tooling/` и `tooling_regressions.py`; переносить только app/ недостаточно. Отчёты не перезаписываются. Все функции, включая тестовые, проверяются Ruff ANN.

API: GET /health; POST /tasks; GET /tasks/{task_id}; PATCH /tasks/{task_id}/status. PATCH принимает ровно status=todo|done; сохраняет id/title; неизвестный UUID — 404; невалидный ввод — 422.

Rules v2: [AGENTS.md](AGENTS.md). Они сохранены без изменения, включая исторический V1 marker. Skills/subagent configuration также сохранены. Codex CLI и модель для проверок не вызываются.
