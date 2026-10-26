"""Task use cases tested independently from FastAPI."""

from uuid import UUID, uuid4

import pytest

from bublik.application.service import TaskService
from bublik.domain.errors import InvalidTaskTitleError, TaskNotFoundError
from bublik.domain.task import Task


class RecordingRepository:
    """Small port implementation recording persistence calls."""

    def __init__(self) -> None:
        self.saved: list[Task] = []

    def save(self, task: Task) -> None:
        self.saved.append(task)

    def get(self, task_id: UUID) -> Task | None:
        return next((task for task in self.saved if task.id == task_id), None)


def test_create_normalizes_persists_and_can_be_retrieved() -> None:
    repository = RecordingRepository()
    service = TaskService(repository)
    task = service.create_task("  Bublik  ")
    assert task.title == "Bublik"
    assert repository.saved == [task]
    assert service.get_task(task.id) == task


def test_creation_generates_distinct_identifiers() -> None:
    service = TaskService(RecordingRepository())
    assert service.create_task("First").id != service.create_task("Second").id


def test_invalid_title_does_not_reach_storage() -> None:
    repository = RecordingRepository()
    with pytest.raises(InvalidTaskTitleError):
        TaskService(repository).create_task("  ")
    assert repository.saved == []


def test_missing_task_raises_typed_error() -> None:
    task_id = uuid4()
    with pytest.raises(TaskNotFoundError) as captured:
        TaskService(RecordingRepository()).get_task(task_id)
    assert captured.value.task_id == task_id
    assert str(captured.value) == "Task not found"
