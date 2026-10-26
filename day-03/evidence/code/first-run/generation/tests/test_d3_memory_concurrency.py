"""Multiple task identities survive concurrent storage and selective replacement."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4

from bublik.domain.task import Task, TaskStatus
from bublik.infrastructure.memory_repository import InMemoryTaskRepository


def test_parallel_save_and_read_preserves_every_distinct_task() -> None:
    repository = InMemoryTaskRepository()
    tasks = [Task(id=uuid4(), title=f"Task {index}") for index in range(64)]

    def save_and_read(task: Task) -> Task | None:
        repository.save(task)
        return repository.get(task.id)

    with ThreadPoolExecutor(max_workers=8) as executor:
        retrieved = list(executor.map(save_and_read, tasks))

    assert retrieved == tasks
    assert [repository.get(task.id) for task in tasks] == tasks


def test_replacing_one_identity_preserves_its_sibling_with_the_same_title() -> None:
    repository = InMemoryTaskRepository()
    original = Task(id=uuid4(), title="Shared title")
    sibling = Task(id=uuid4(), title="Shared title")
    repository.save(original)
    repository.save(sibling)
    updated = replace(original, status=TaskStatus.DONE)

    repository.save(updated)

    assert repository.get(original.id) == updated
    assert repository.get(sibling.id) == sibling
    assert repository.get(sibling.id).status is TaskStatus.TODO
    assert original.status is TaskStatus.TODO
