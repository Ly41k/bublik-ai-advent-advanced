"""Fresh application state for each API test."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bublik.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Exercise HTTP in process without opening a network port."""
    with TestClient(create_app()) as test_client:
        yield test_client
