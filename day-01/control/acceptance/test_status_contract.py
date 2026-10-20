"""Frozen behavioral acceptance for the future endpoint, not baseline tests."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from bublik.main import create_app


@pytest.fixture
def api() -> Iterator[TestClient]:
    with TestClient(create_app()) as client:
        yield client


def test_status_round_trip_and_repeated_requests(api: TestClient) -> None:
    created = api.post("/tasks", json={"title": "Keep this title"})
    assert created.status_code == 201
    task = created.json()
    for desired in ("todo", "done", "done", "todo", "todo"):
        response = api.patch(f"/tasks/{task['id']}/status", json={"status": desired})
        assert response.status_code == 200
        assert response.json() == {**task, "status": desired}
        read_back = api.get(f"/tasks/{task['id']}")
        assert read_back.status_code == 200
        assert read_back.json() == response.json()


def test_unknown_task_returns_exact_error(api: TestClient) -> None:
    response = api.patch(f"/tasks/{uuid4()}/status", json={"status": "done"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_malformed_identifier_is_rejected(api: TestClient) -> None:
    assert api.patch("/tasks/not-a-uuid/status", json={"status": "done"}).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "doing"},
        {"status": "DONE"},
        {"status": " done "},
        {"status": ""},
        {"status": None},
        {"status": 1},
        {"status": True},
        {"status": ["done"]},
        {"status": {"value": "done"}},
        {"status": "done", "title": "Override"},
        {"status": "done", "id": str(uuid4())},
    ],
)
def test_invalid_payload_does_not_change_storage(
    api: TestClient, payload: dict[str, object]
) -> None:
    task = api.post("/tasks", json={"title": "Unchanged"}).json()
    assert api.patch(f"/tasks/{task['id']}/status", json=payload).status_code == 422
    assert api.get(f"/tasks/{task['id']}").json() == task


def test_missing_body_is_rejected_without_changing_task(api: TestClient) -> None:
    task = api.post("/tasks", json={"title": "Unchanged"}).json()
    assert api.patch(f"/tasks/{task['id']}/status").status_code == 422
    assert api.get(f"/tasks/{task['id']}").json() == task


def test_update_does_not_change_another_task(api: TestClient) -> None:
    first = api.post("/tasks", json={"title": "First"}).json()
    second = api.post("/tasks", json={"title": "Second"}).json()
    assert api.patch(f"/tasks/{first['id']}/status", json={"status": "done"}).status_code == 200
    assert api.get(f"/tasks/{second['id']}").json() == second
