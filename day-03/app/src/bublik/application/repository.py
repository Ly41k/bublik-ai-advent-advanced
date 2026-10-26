"""Storage port consumed by the task service."""

from typing import Protocol
from uuid import UUID

from bublik.domain.task import Task


class TaskRepository(Protocol):
    """Store tasks by identifier; save replaces an existing value."""

    def save(self, task: Task) -> None:
        """Persist the complete task value."""
        ...

    def get(self, task_id: UUID) -> Task | None:
        """Return a task, or None when it is absent."""
        ...
