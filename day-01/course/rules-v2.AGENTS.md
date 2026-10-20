# Bublik — project Rules v1

Startup instruction marker: `BUBLIK_PROJECT_RULES_V1_20261020`.

## Purpose and scope

Build the independent Bublik Task Service for AI Advent Challenge Advanced.
Use the public name Bublik. Keep the accepted baseline tag immutable.
Do only the requested task; do not add databases, external providers, CI or
workflow infrastructure. Do not run controlled generations during Gate 2.

## Stack and commands

Python **3.13.3**, FastAPI, Pydantic v2, pytest, Ruff, in-memory storage.
Mac experiment: **Codex CLI 0.163.0**, ChatGPT login. Exact dependencies:
`requirements.lock` and `uv.lock`. Use the existing `.venv`; never update the
client, install new packages or regenerate locks during the experiment.

Installation, only when separately requested:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
```

Local startup:

```bash
python -m uvicorn bublik.main:create_app --factory --host 127.0.0.1 --port 8000
```

After code changes, use `$quality-gate` with an explicit report path. Fixed checks:

```bash
python -m compileall -q src tests scripts
python -c "from bublik.main import create_app; create_app()"
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

`scripts/run_checks.py --output <permitted-path>` records command exit codes.
No PASS without observed results. Preserve earlier failed reports.

## Structure and architecture

| Path | Responsibility |
| --- | --- |
| `src/bublik/domain/` | Immutable Task/TaskStatus, validation and typed errors; stdlib only |
| `src/bublik/application/` | TaskService and TaskRepository protocol |
| `src/bublik/infrastructure/` | InMemoryTaskRepository adapter |
| `src/bublik/api/` | HTTP routes, Pydantic DTOs, DI accessor |
| `src/bublik/main.py` | Composition root; constructs service and storage |
| `tests/` | Domain, service, storage, HTTP and static import checks |
| `scripts/` | Baseline deterministic checks |
| `gate2/` | Frozen protocol, acceptance tests, diagnostic tools |
| `.agents/skills/` | Repeatable procedures |
| `.codex/` | Runtime and specialized agent configuration |
| `weeks/week-01/` | Reports and evidence, not application input |

API depends on application/domain. Application depends on domain and the
repository port, never on API, FastAPI, Pydantic, main or infrastructure.
Domain never imports higher layers/frameworks. API never constructs concrete
storage or imports main. Main alone wires implementations. Static boundary
tests do not establish restrictions against arbitrary dynamic imports.

## Naming and patterns

Use absolute imports, `snake_case` modules/functions, `PascalCase` types,
`UPPER_CASE` enum members, and `test_<behavior>` tests. Add parameter and return
annotations; avoid unnecessary `__all__` or wildcard exports.
Keep DTOs in API and use explicit response models. Business decisions belong
in the service/domain. Inject storage through its Protocol. Map expected domain
errors to HTTP errors. Use normal `def` for synchronous operations; introduce
`async def` only for actual asynchronous I/O. Keep mutable storage per app.
Use fresh TestClient instances without external requests in tests.

## Five examples from the accepted baseline

1. `src/bublik/domain/task.py#Task`:

   ```python
   @dataclass(frozen=True, slots=True)
   class Task:
   ```

   Immutable domain values protect state outside HTTP/storage details.

2. `src/bublik/application/repository.py#TaskRepository`:

   ```python
   class TaskRepository(Protocol):
       """Store tasks by identifier; save replaces an existing value."""
   ```

   Consume a typed port rather than a concrete adapter.

3. `src/bublik/application/service.py#TaskService.get_task`:

   ```python
   task = self._repository.get(task_id)
   if task is None:
       raise TaskNotFoundError(task_id)
   return task
   ```

   Keep HTTP status codes out of use cases with a typed absence error.

4. `src/bublik/api/routes.py#get_task`:

   ```python
   except TaskNotFoundError as error:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
   ```

   Handle expected errors without hiding unrelated exceptions.

5. `tests/test_api.py#test_application_instances_do_not_share_tasks`:

   ```python
   with TestClient(create_app()) as second_client:
       assert second_client.get(f"/tasks/{task_id}").status_code == 404
   ```

   Verify independent application state through HTTP behavior.

## Five antipatterns and alternatives

1. Business logic/repository construction in routes → TaskService and main wiring.
2. `except Exception: pass` or invented success → typed errors and honest failures.
3. Unexplained `Any`, untyped `dict`, wildcard imports → explicit DTO/domain/Protocol types.
4. Global mutable task storage or bypassed domain validation → per-app storage
   and validated immutable values.
5. Editing old tests/locks/Rules to get green checks, hardcoded credentials or
   unsolicited external actions → protected inputs, new behavioral tests,
   preserved failures and actions within the authorized scope.

## Typical application module

```python
"""Describe the use case and its boundary."""

from uuid import UUID

from bublik.application.repository import TaskRepository
from bublik.domain.errors import TaskNotFoundError
from bublik.domain.task import Task


class ExampleService:
    """Describe the public responsibility."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def get_task(self, task_id: UUID) -> Task:
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
```

Order: docstring, stdlib imports, third-party imports if needed, project imports,
types and public class/function. Keep the public interface small; do not add
exports merely to imitate another language.

## Delegation and quality gate

When invoking ArchitectureReportAgent, use agent_type="architecture_report"
and task_name="architecture_report" so the task name identifies its returned
ArchitectureReport type. Keep the existing entry and result contracts.

Use configured `architecture_report` (ArchitectureReportAgent) for bounded
review returning `ArchitectureReport`. Pass all required inputs: `task_spec`,
`repo_root`, `review_scope`, `architecture_rules`. Full entry/result contract:
`.codex/agents/architecture_report.toml`. Missing input requires immediate
`MISSING_REQUIRED_INPUT`, zero tool calls and no invented defaults. Distinguish
input, execution and output-validation errors. Wait for and validate its result.
For the explicitly authorized missing-input diagnostic only, forward the given
incomplete object unchanged so the child can demonstrate its fail-fast contract.

The agent reviews and returns. The orchestrator owns implementation, aggregation,
validation and the decision. Use at most one concurrent subagent, without
recursion or delegation for its own sake. Agent instructions are not an enforced
read-only sandbox: native subagents inherit parent permissions.

`quality-gate`: `.agents/skills/quality-gate/SKILL.md`. Supply explicit inputs
and report actual results. Tests and architecture review complement each other.

## Safety and completion

Do not expose credentials, read private auth files, publish, push, merge or use
external services without authorization. Do not change global settings during
implementation. Preserve existing tests, locks, experiment inputs and Rules,
unless the current Gate explicitly authorizes their revision. Report conflicts
instead of silently dropping invariants. DONE requires validation; otherwise
report BLOCKED/FAILED with evidence.
