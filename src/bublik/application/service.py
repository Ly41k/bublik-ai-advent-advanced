"""Task use cases independent of HTTP and storage implementation."""

from uuid import UUID, uuid4

from bublik.application.repository import TaskRepository
from bublik.domain.errors import TaskNotFoundError
from bublik.domain.task import Task


class TaskService:
    """Create and retrieve tasks through a repository port."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def create_task(self, title: str) -> Task:
        """Validate a new task and persist it with a generated identifier."""
        task = Task(id=uuid4(), title=title)
        self._repository.save(task)
        return task

    def get_task(self, task_id: UUID) -> Task:
        """Return a task or raise a typed domain error."""
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
