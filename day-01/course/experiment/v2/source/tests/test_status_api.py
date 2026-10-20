"""Status endpoint contract and persistence through HTTP in process."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def test_status_transitions_and_repeated_updates(client: TestClient):
    original = client.post("/tasks", json={"title": "  Keep identity  "}).json()
    other = client.post("/tasks", json={"title": "Other"}).json()

    for target in ("todo", "done", "done", "todo", "todo"):
        response = client.patch(f"/tasks/{original['id']}/status", json={"status": target})
        expected = {**original, "status": target}
        assert response.status_code == 200
        assert response.json() == expected
        fetched = client.get(f"/tasks/{original['id']}")
        assert fetched.status_code == 200
        assert fetched.json() == expected
        assert client.get(f"/tasks/{other['id']}").json() == other


def test_unknown_status_task(client: TestClient):
    original = client.post("/tasks", json={"title": "Existing"}).json()
    response = client.patch(f"/tasks/{uuid4()}/status", json={"status": "done"})
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
        {"status": " done "},
        {"status": None},
        {"status": 1},
        {"status": True},
        {"status": ["done"]},
        {"status": {"value": "done"}},
        {"status": "done", "title": "Changed"},
        {"status": "todo", "id": str(uuid4())},
        None,
        ["done"],
        "done",
    ],
)
def test_invalid_status_payload_preserves_tasks(
    client: TestClient, initial_status: str, payload: object
):
    original = client.post("/tasks", json={"title": "Unchanged"}).json()
    other = client.post("/tasks", json={"title": "Other"}).json()
    setup = client.patch(f"/tasks/{original['id']}/status", json={"status": initial_status})
    assert setup.status_code == 200
    expected = {**original, "status": initial_status}

    response = client.patch(f"/tasks/{original['id']}/status", json=payload)

    assert response.status_code == 422
    assert client.get(f"/tasks/{original['id']}").json() == expected
    assert client.get(f"/tasks/{other['id']}").json() == other


def test_invalid_status_task_identifier_preserves_task(client: TestClient):
    original = client.post("/tasks", json={"title": "Existing"}).json()
    response = client.patch("/tasks/not-a-uuid/status", json={"status": "done"})
    assert response.status_code == 422
    assert client.get(f"/tasks/{original['id']}").json() == original
