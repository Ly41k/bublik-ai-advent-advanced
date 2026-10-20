"""HTTP contract and persistence for task status updates."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def test_status_updates_in_both_directions_and_repeated_updates(client: TestClient) -> None:
    original = client.post("/tasks", json={"title": "  First task  "}).json()
    other = client.post("/tasks", json={"title": "Other task"}).json()
    path = f"/tasks/{original['id']}"

    for status in ("todo", "done", "done", "todo"):
        response = client.patch(f"{path}/status", json={"status": status})
        expected = {**original, "status": status}
        assert response.status_code == 200
        assert response.json() == expected
        fetched = client.get(path)
        assert fetched.status_code == 200
        assert fetched.json() == expected
        assert client.get(f"/tasks/{other['id']}").json() == other


@pytest.mark.parametrize("status", ["todo", "done"])
def test_unknown_task_status_update(client: TestClient, status: str) -> None:
    original = client.post("/tasks", json={"title": "Existing task"}).json()
    response = client.patch(f"/tasks/{uuid4()}/status", json={"status": status})
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
    assert client.get(f"/tasks/{original['id']}").json() == original


@pytest.mark.parametrize("initial_status", ["todo", "done"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "invalid"},
        {"status": "DONE"},
        {"status": ""},
        {"status": " done "},
        {"status": None},
        {"status": 1},
        {"status": True},
        {"status": []},
        {"status": {}},
        {"status": "done", "title": "Changed title"},
        {"status": "done", "id": str(uuid4())},
        {"status": "done", "extra": "value"},
        None,
        [],
        "done",
    ],
)
def test_invalid_status_payload_preserves_task(
    client: TestClient, initial_status: str, payload: object
) -> None:
    original = client.post("/tasks", json={"title": "Unchanged task"}).json()
    path = f"/tasks/{original['id']}"
    assert client.patch(f"{path}/status", json={"status": initial_status}).status_code == 200
    expected = {**original, "status": initial_status}

    assert client.patch(f"{path}/status", json=payload).status_code == 422
    assert client.get(path).json() == expected


def test_invalid_status_task_identifier_preserves_task(client: TestClient) -> None:
    original = client.post("/tasks", json={"title": "Unchanged task"}).json()
    response = client.patch("/tasks/not-a-uuid/status", json={"status": "done"})
    assert response.status_code == 422
    assert client.get(f"/tasks/{original['id']}").json() == original
