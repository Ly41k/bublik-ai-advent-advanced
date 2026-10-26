"""Task title invariants remain true outside the HTTP layer."""

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from bublik.domain.errors import InvalidTaskTitleError
from bublik.domain.task import Task, TaskStatus


def test_title_is_trimmed_and_new_task_is_todo() -> None:
    task = Task(id=uuid4(), title="  Learn Rules  ")
    assert task.title == "Learn Rules"
    assert task.status is TaskStatus.TODO


@pytest.mark.parametrize("title", ["", "   ", "\t\n", "a" * 201])
def test_invalid_title_is_rejected(title: str) -> None:
    with pytest.raises(InvalidTaskTitleError):
        Task(id=uuid4(), title=title)


@pytest.mark.parametrize("title", ["a", "a" * 200, "  " + "a" * 200 + "  "])
def test_title_boundaries_apply_after_trimming(title: str) -> None:
    assert Task(id=uuid4(), title=title).title == title.strip()


def test_task_is_immutable() -> None:
    task = Task(id=uuid4(), title="Keep the baseline")
    with pytest.raises(FrozenInstanceError):
        task.title = "Mutated"
