import pytest
from fastapi.testclient import TestClient

from todo_api.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
