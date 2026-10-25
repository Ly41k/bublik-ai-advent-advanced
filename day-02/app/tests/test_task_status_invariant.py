"""Task status invariants hold on construction and dataclass replacement."""

from dataclasses import replace
from uuid import uuid4

import pytest

from bublik.domain.errors import InvalidTaskStatusError
from bublik.domain.task import Task, TaskStatus


@pytest.mark.parametrize("status", [None, 42, "invalid-status", [], {}])
def test_constructor_rejects_invalid_status(status: object) -> None:
    with pytest.raises(InvalidTaskStatusError):
        Task(id=uuid4(), title="Valid title", status=status)


@pytest.mark.parametrize("status", [None, 42, "invalid-status", [], {}])
def test_replace_rejects_invalid_status(status: object) -> None:
    original = Task(id=uuid4(), title="Valid title")

    with pytest.raises(InvalidTaskStatusError):
        replace(original, status=status)

    assert original.status is TaskStatus.TODO


@pytest.mark.parametrize("status", [TaskStatus.TODO, TaskStatus.DONE])
def test_supported_status_survives_construction_and_replace(status: TaskStatus) -> None:
    task = Task(id=uuid4(), title="Valid title", status=status)

    assert task.status is status
    updated = replace(task, status=status)
    assert updated.status is status
    assert updated.id == task.id
    assert updated.title == task.title


def test_default_status_is_todo() -> None:
    assert Task(id=uuid4(), title="Valid title").status is TaskStatus.TODO
