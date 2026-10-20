# Actual baseline code references for future Rules

These symbols exist in this repository before either controlled generation.
They are candidate examples, not a replacement for Gate 2 AGENTS.md v1.
Use the baseline commit and symbol anchors to avoid stale line references.

## 1. Immutable domain entity

Source: `src/bublik/domain/task.py`, `Task` and `Task.__post_init__`.

```python
@dataclass(frozen=True, slots=True)
class Task:
```

The entity normalizes and validates its title independently of Pydantic and
FastAPI. Frozen values cannot expose mutable task state through the repository.

## 2. Repository port

Source: `src/bublik/application/repository.py`, `TaskRepository`.

```python
class TaskRepository(Protocol):
```

The application consumes typed `save(Task)` and `get(UUID)` operations. Its
service does not construct or import the in-memory implementation.

## 3. Application use case

Source: `src/bublik/application/service.py`, `TaskService.get_task`.

```python
task = self._repository.get(task_id)
if task is None:
    raise TaskNotFoundError(task_id)
return task
```

Absence is converted to a typed error at the use-case boundary, without HTTP
status codes or exception swallowing.

## 4. Thin transport and error mapping

Source: `src/bublik/api/routes.py`, `get_task`.

```python
except TaskNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
```

The HTTP handler uses DI, delegates to the service, and catches only the
expected domain error. Request/response schemas are explicit.

## 5. Isolated API verification

Source: `tests/test_api.py`, `test_application_instances_do_not_share_tasks`;
fixture: `tests/conftest.py`, `client`.

```python
with TestClient(create_app()) as second_client:
    assert second_client.get(f"/tasks/{task_id}").status_code == 404
```

A real second ASGI application confirms state isolation; the fixture also
creates a fresh app per test. No public server or external API is used.
