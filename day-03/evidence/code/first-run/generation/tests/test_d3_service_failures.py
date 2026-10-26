"""Storage failure propagation and validation order in the task use cases."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from bublik.application.repository import TaskRepository
from bublik.application.service import TaskService
from bublik.domain.errors import InvalidTaskStatusError
from bublik.domain.task import Task, TaskStatus


def test_create_propagates_original_storage_failure() -> None:
    repository = Mock(spec=TaskRepository)
    failure = OSError("Storage write unavailable")
    repository.save.side_effect = failure

    with pytest.raises(OSError) as captured:
        TaskService(repository).create_task("  Keep failure identity  ")

    assert captured.value is failure
    repository.save.assert_called_once()
    attempted = repository.save.call_args.args[0]
    assert attempted.title == "Keep failure identity"
    assert attempted.status is TaskStatus.TODO
    repository.get.assert_not_called()


def test_get_propagates_read_failure_instead_of_not_found() -> None:
    repository = Mock(spec=TaskRepository)
    failure = OSError("Storage read unavailable")
    repository.get.side_effect = failure
    task_id = uuid4()

    with pytest.raises(OSError) as captured:
        TaskService(repository).get_task(task_id)

    assert captured.value is failure
    repository.get.assert_called_once_with(task_id)
    repository.save.assert_not_called()


def test_failed_update_does_not_mutate_the_original_value() -> None:
    repository = Mock(spec=TaskRepository)
    original = Task(id=uuid4(), title="Original")
    repository.get.return_value = original
    failure = OSError("Status write unavailable")
    repository.save.side_effect = failure

    with pytest.raises(OSError) as captured:
        TaskService(repository).update_task_status(original.id, TaskStatus.DONE)

    assert captured.value is failure
    repository.get.assert_called_once_with(original.id)
    repository.save.assert_called_once_with(
        Task(id=original.id, title=original.title, status=TaskStatus.DONE)
    )
    assert original.status is TaskStatus.TODO


def test_invalid_status_is_rejected_before_repository_access() -> None:
    repository = Mock(spec=TaskRepository)
    repository.get.side_effect = OSError("Must not read")

    with pytest.raises(InvalidTaskStatusError):
        TaskService(repository).update_task_status(uuid4(), "unsupported")

    repository.get.assert_not_called()
    repository.save.assert_not_called()
