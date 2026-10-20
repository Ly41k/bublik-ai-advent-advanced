"""Thread-safe in-memory task storage scoped to one application."""

from threading import Lock
from uuid import UUID

from bublik.domain.task import Task


class InMemoryTaskRepository:
    """Keep immutable values in memory; restarting the app clears them."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        self._lock = Lock()

    def save(self, task: Task) -> None:
        """Insert or replace one complete task value."""
        with self._lock:
            self._tasks[task.id] = task

    def get(self, task_id: UUID) -> Task | None:
        """Read a value without exposing the mutable storage container."""
        with self._lock:
            return self._tasks.get(task_id)
