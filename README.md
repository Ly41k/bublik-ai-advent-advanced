# Bublik Task Service — AI Advent Challenge Advanced

## Day 1 — Rules: Course Minimum PASS

Чистовая рабочая копия: [`day-01/app/`](day-01/app/).
Полная документация: [Day 1 — README](day-01/README_RU.md).

- [Матрица обязательных требований: 25/25 PASS](day-01/course/REQUIREMENTS_RU.md).
- [Финальная Mac-приёмка](day-01/course/FINAL_MAC_ACCEPTANCE_RU.md).
- [Сравнение независимых Rules v1/v2](day-01/course/COMPARISON_RU.md).
- [Фактический Mac Quality Gate JSON](day-01/proof/mac-final-2026-10-20/mac-foundation-001.json).

Mac Darwin arm64 / Python 3.13.3: compile/import/Ruff lint+annotations/format PASS;
97 pytest, 17/17 внешних acceptance cases; native trace/E1/contracts: 102/7/5 PASS.
Обе исторические генерации прошли 17/17 acceptance. Уточнение Rules v2 исправило
имя делегированной задачи; улучшение функциональности не заявляется. Исторический
FAIL v2 по семи аннотациям сохранён; чистовая копия исправлена отдельно.

Baseline commit/tag сохранены. Приватные native sessions, auth и оригиналы
скриншотов с локальными путями не публикуются; приёмка и SHA доказательств приложены.
Advanced Maximum — DEFERRED; Bublik Ready — отдельная будущая оценка.

## Историческое описание Gate 1 baseline

Корневые src/tests и заметки ниже относятся к неизменённому исходному baseline,
а не к актуальной чистовой приёмке Day 1. Для работы и запуска используйте day-01/app/.


Independent training project: <https://github.com/Ly41k/bublik-ai-advent-advanced>.
No runtime dependency on the previous AI Advent repository.

Gate 1 provides a small baseline. The Rules v1/v2 experiment has **not** run.
The future status-change endpoint is intentionally absent.

## Environment and reproducible setup

Use **Python 3.13.3**. Mac Codex CLI **0.163.0** is confirmed by the user;
keep that version unchanged during the experiment. Do not update dependencies
or regenerate either lockfile between runs.

`uv.lock` is the universal resolver lock; `requirements.lock` is its hashed
export, including development/build dependencies. The commands below need
Python and pip, without requiring uv on the Mac:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python scripts/run_checks.py --output local-evidence/mac-baseline-checks.txt
```

The installed Python must report `3.13.3` before setup. Initial dependency
installation needs network access; the service and verification checks do not.
If Python or a locked wheel is unavailable, report the failure rather than
changing versions silently. Mac execution remains unverified until its log is reviewed.

## Run locally

```bash
python -m uvicorn bublik.main:create_app --factory --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' --data '{"title":"Learn Rules"}'
```

Copy the returned UUID and call `GET /tasks/<UUID>`. Swagger UI is available at
<http://127.0.0.1:8000/docs>. Data belongs to one app instance, disappears on
restart, and is not shared across workers. Use one worker for this baseline.

| Endpoint | Contract |
| --- | --- |
| `GET /health` | `200`, `{"status":"ok"}` |
| `POST /tasks` | JSON `{"title":"..."}`; `201`, `{id,title,status}`; UUID4 and `todo` |
| `GET /tasks/{task_id}` | `200`, saved task; missing UUID → `404`, `{"detail":"Task not found"}` |

Titles are strings trimmed before enforcing 1–200 characters. Missing, blank,
oversized, non-string titles and extra create fields return `422`.
A malformed path UUID also returns `422`.

## Structure and dependencies

| Directory | Responsibility |
| --- | --- |
| `src/bublik/domain/` | Immutable Task, statuses, validation, typed errors; standard library only |
| `src/bublik/application/` | Use cases and the TaskRepository protocol; depends on domain |
| `src/bublik/infrastructure/` | In-memory repository; domain values, no HTTP |
| `src/bublik/api/` | Pydantic DTOs, DI accessor, thin HTTP handlers |
| `src/bublik/main.py` | Composition root; wires concrete storage and service |
| `tests/` | Domain, service, storage, HTTP, and import-boundary checks |
| `scripts/` | Deterministic local verification; no model calls |
| `docs/` | Baseline code references and Mac handoff |
| `weeks/week-01/` | Gate reports and recorded evidence |

Use absolute imports, `snake_case` modules/functions, `PascalCase` types,
`UPPER_CASE` enum members, explicit DTOs and return types. Synchronous handlers
match the synchronous in-memory service; do not add async wrappers without I/O.
Only the composition root constructs the concrete repository. API imports the
application layer, while application and domain never import API or infrastructure.

## Verification

```bash
python -m compileall -q src tests scripts
python -c "from bublik.main import create_app; create_app()"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

`scripts/run_checks.py` runs these commands, logs stdout/stderr, exit codes,
environment/package versions, and a source/config SHA-256 manifest. It continues
after a failed check and exits nonzero if any check fails. Output must be under
`local-evidence/` or `weeks/week-01/evidence/day-01/`. The log is sanitized for
local home/workspace/virtualenv paths and contains no credential inventory.

## Gate boundaries

Real code references: `docs/BASELINE_CODE_EXAMPLES.md`.
Transfer instructions: `docs/MAC_HANDOFF.md`.
Status: `weeks/week-01/DAY_01.md`.

Gate 2 must verify actual global/project instructions, the project skill, and
the configured native subagent. This baseline contains no Rules snapshots,
project skills, agent TOMLs, or status-change implementation. Do not run
Generation 1 or Generation 2 yet. Push, PR publication, and merge need separate approval.
