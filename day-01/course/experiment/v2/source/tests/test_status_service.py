"""Status use cases through a recording implementation of the repository port."""

from uuid import UUID, uuid4

import pytest

from bublik.application.service import TaskService
from bublik.domain.errors import InvalidTaskStatusError, TaskNotFoundError
from bublik.domain.task import Task, TaskStatus


class StatusRepository:
    """Record writes and implement the port's replacement semantics."""

    def __init__(self) -> None:
        self.tasks: dict[UUID, Task] = {}
        self.writes: list[Task] = []

    def save(self, task: Task) -> None:
        self.tasks[task.id] = task
        self.writes.append(task)

    def get(self, task_id: UUID) -> Task | None:
        return self.tasks.get(task_id)


@pytest.mark.parametrize(
    ("initial", "target"),
    [
        (TaskStatus.TODO, TaskStatus.DONE),
        (TaskStatus.DONE, TaskStatus.TODO),
        (TaskStatus.TODO, TaskStatus.TODO),
        (TaskStatus.DONE, TaskStatus.DONE),
    ],
)
def test_status_update_persists_and_preserves_other_values(initial: TaskStatus, target: TaskStatus):
    repository = StatusRepository()
    original = Task(id=uuid4(), title="Original title", status=initial)
    other = Task(id=uuid4(), title="Other task")
    repository.save(original)
    repository.save(other)
    service = TaskService(repository)

    updated = service.update_task_status(original.id, target)

    assert updated == Task(id=original.id, title=original.title, status=target)
    assert service.get_task(original.id) == updated
    assert repository.writes[-1] == updated
    assert service.get_task(other.id) == other
    assert original.status == initial


def test_unknown_status_task_raises_without_writing():
    repository = StatusRepository()
    service = TaskService(repository)
    existing = service.create_task("Existing")
    previous_writes = repository.writes.copy()
    missing_id = uuid4()

    with pytest.raises(TaskNotFoundError) as captured:
        service.update_task_status(missing_id, TaskStatus.DONE)

    assert captured.value.task_id == missing_id
    assert str(captured.value) == "Task not found"
    assert repository.writes == previous_writes
    assert service.get_task(existing.id) == existing


@pytest.mark.parametrize("invalid_status", ["invalid", "", None, 1, True, [], {}])
def test_invalid_status_does_not_write(invalid_status: object):
    repository = StatusRepository()
    service = TaskService(repository)
    task = service.create_task("Unchanged")
    previous_writes = repository.writes.copy()

    with pytest.raises(InvalidTaskStatusError):
        service.update_task_status(task.id, invalid_status)

    assert repository.writes == previous_writes
    assert service.get_task(task.id) == task
