"""Observable storage behavior of the in-memory adapter."""

from dataclasses import replace
from uuid import uuid4

from bublik.domain.task import Task
from bublik.infrastructure.memory_repository import InMemoryTaskRepository


def test_save_and_get_round_trip():
    task = Task(id=uuid4(), title="Stored task")
    repository = InMemoryTaskRepository()
    repository.save(task)
    assert repository.get(task.id) == task


def test_missing_task_returns_none():
    assert InMemoryTaskRepository().get(uuid4()) is None


def test_save_replaces_the_complete_value_without_mutating_old_value():
    task = Task(id=uuid4(), title="Original")
    replacement = replace(task, title="Replacement")
    repository = InMemoryTaskRepository()
    repository.save(task)
    repository.save(replacement)
    assert repository.get(task.id) == replacement
    assert task.title == "Original"


def test_repositories_have_independent_storage():
    task = Task(id=uuid4(), title="Private to one app")
    first = InMemoryTaskRepository()
    first.save(task)
    assert InMemoryTaskRepository().get(task.id) is None
