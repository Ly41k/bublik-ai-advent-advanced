"""Errors understood by the application and transport layers."""

from uuid import UUID


class InvalidTaskTitleError(ValueError):
    """A title is blank or exceeds the domain limit."""


class TaskNotFoundError(LookupError):
    """A task with the requested identifier does not exist."""

    def __init__(self, task_id: UUID) -> None:
        self.task_id = task_id
        super().__init__("Task not found")
