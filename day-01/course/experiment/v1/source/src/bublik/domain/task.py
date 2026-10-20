"""Immutable task entity and its allowed statuses."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from bublik.domain.errors import InvalidTaskTitleError


class TaskStatus(StrEnum):
    """Statuses understood by Bublik."""

    TODO = "todo"
    DONE = "done"


@dataclass(frozen=True, slots=True)
class Task:
    """A task with a normalized title of 1–200 characters."""

    id: UUID
    title: str
    status: TaskStatus = TaskStatus.TODO

    def __post_init__(self) -> None:
        title = self.title.strip()
        if not 1 <= len(title) <= 200:
            raise InvalidTaskTitleError("Task title must contain 1–200 characters")
        object.__setattr__(self, "title", title)
