"""Task use cases independent of HTTP and storage implementation."""

from dataclasses import replace
from uuid import UUID, uuid4

from bublik.application.repository import TaskRepository
from bublik.domain.errors import InvalidTaskStatusError, TaskNotFoundError
from bublik.domain.task import Task, TaskStatus


class TaskService:
    """Create, retrieve and update tasks through a repository port."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def create_task(self, title: str) -> Task:
        """Validate a new task and persist it with a generated identifier."""
        task = Task(id=uuid4(), title=title)
        self._repository.save(task)
        return task

    def update_task_status(self, task_id: UUID, status: TaskStatus) -> Task:
        """Validate and persist a status while preserving task identity and title."""
        try:
            validated_status = TaskStatus(status)
        except (TypeError, ValueError) as error:
            raise InvalidTaskStatusError("Invalid task status") from error
        task = self.get_task(task_id)
        updated = replace(task, status=validated_status)
        self._repository.save(updated)
        return updated

    def get_task(self, task_id: UUID) -> Task:
        """Return a task or raise a typed domain error."""
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
