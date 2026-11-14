import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["env"] == "development"


@pytest.mark.asyncio
async def test_create_task_persists(client):
    payload = {"title": "Revisar SQLAlchemy async", "description": "Dia 2"}
    response = await client.post("/tasks", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Revisar SQLAlchemy async"
    assert data["done"] is False
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_create_task_rejects_empty_title(client):
    response = await client.post("/tasks", json={"title": ""})
    assert response.status_code == 422
