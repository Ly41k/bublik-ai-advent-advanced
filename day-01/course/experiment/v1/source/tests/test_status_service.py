"""Status updates through the application service and repository port."""

from uuid import UUID, uuid4

import pytest

from bublik.application.service import TaskService
from bublik.domain.errors import TaskNotFoundError
from bublik.domain.task import Task, TaskStatus


class RecordingRepository:
    """Implement replacement semantics and record writes through the port."""

    def __init__(self) -> None:
        self.tasks: dict[UUID, Task] = {}
        self.saved: list[Task] = []

    def save(self, task: Task) -> None:
        self.tasks[task.id] = task
        self.saved.append(task)

    def get(self, task_id: UUID) -> Task | None:
        return self.tasks.get(task_id)


def test_status_transitions_are_persisted_and_preserve_other_values() -> None:
    repository = RecordingRepository()
    service = TaskService(repository)
    original = service.create_task("First task")
    other = service.create_task("Other task")

    for status in (TaskStatus.TODO, TaskStatus.DONE, TaskStatus.DONE, TaskStatus.TODO):
        updated = service.update_task_status(original.id, status)
        assert updated == Task(id=original.id, title=original.title, status=status)
        assert repository.saved[-1] == updated
        assert service.get_task(original.id) == updated
        assert service.get_task(other.id) == other

    assert original.status is TaskStatus.TODO


def test_unknown_task_status_update_does_not_write() -> None:
    repository = RecordingRepository()
    service = TaskService(repository)
    original = service.create_task("Existing task")
    task_id = uuid4()

    with pytest.raises(TaskNotFoundError) as captured:
        service.update_task_status(task_id, TaskStatus.DONE)

    assert captured.value.task_id == task_id
    assert str(captured.value) == "Task not found"
    assert repository.saved == [original]
    assert service.get_task(original.id) == original


@pytest.mark.parametrize("status", ["invalid", "DONE", "", None, 1, True, [], {}])
def test_invalid_service_status_does_not_write(status: TaskStatus) -> None:
    repository = RecordingRepository()
    service = TaskService(repository)
    original = service.create_task("Unchanged task")

    with pytest.raises(ValueError):
        service.update_task_status(original.id, status)

    assert repository.saved == [original]
    assert service.get_task(original.id) == original
