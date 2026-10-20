"""Baseline HTTP behavior and validation through the real ASGI app."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from bublik.main import create_app


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_task(client: TestClient):
    created = client.post("/tasks", json={"title": "  Learn Rules  "})
    assert created.status_code == 201
    task = created.json()
    assert set(task) == {"id", "title", "status"}
    assert UUID(task["id"]).version == 4
    assert task["title"] == "Learn Rules"
    assert task["status"] == "todo"
    fetched = client.get(f"/tasks/{task['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == task


@pytest.mark.parametrize("title", ["a", "a" * 200, "  " + "a" * 200 + "  "])
def test_create_title_boundaries(client: TestClient, title: str):
    response = client.post("/tasks", json={"title": title})
    assert response.status_code == 201
    assert response.json()["title"] == title.strip()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": " \t\n "},
        {"title": "a" * 201},
        {"title": None},
        {"title": 123},
        {"title": ["task"]},
        {"title": "Task", "status": "done"},
        {"title": "Task", "id": str(uuid4())},
    ],
)
def test_invalid_create_payload(client: TestClient, payload: dict[str, object]):
    assert client.post("/tasks", json=payload).status_code == 422


def test_unknown_task(client: TestClient):
    response = client.get(f"/tasks/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_invalid_task_identifier(client: TestClient):
    assert client.get("/tasks/not-a-uuid").status_code == 422


def test_application_instances_do_not_share_tasks(client: TestClient):
    task_id = client.post("/tasks", json={"title": "Only in first app"}).json()["id"]
    with TestClient(create_app()) as second_client:
        assert second_client.get(f"/tasks/{task_id}").status_code == 404
