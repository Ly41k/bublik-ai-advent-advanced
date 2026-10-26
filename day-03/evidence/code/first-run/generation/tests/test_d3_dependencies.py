"""Uncovered service-wiring failures at the resolver and HTTP boundary."""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from bublik.api.dependencies import get_task_service
from bublik.main import create_app


def test_resolver_returns_the_exact_application_service() -> None:
    app = create_app()
    request = Request({"type": "http", "app": app})

    assert get_task_service(request) is app.state.task_service


@pytest.mark.parametrize("invalid_service", [None, "not a service", object()])
def test_resolver_rejects_misconfigured_service(invalid_service: object) -> None:
    app = create_app()
    app.state.task_service = invalid_service
    request = Request({"type": "http", "app": app})

    with pytest.raises(TypeError, match="Application task service is not configured"):
        get_task_service(request)


def test_misconfigured_service_fails_http_without_breaking_health() -> None:
    app = create_app()
    app.state.task_service = None

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/tasks", json={"title": "Cannot be stored"})

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
