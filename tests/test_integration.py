import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_create_task_persists_in_postgres(integration_client):
    """Testa a criação de tarefa contra um PostgreSQL real."""
    payload = {"title": "Teste com Testcontainers", "description": "Dia 3"}
    response = await integration_client.post("/tasks", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1
    assert data["title"] == "Teste com Testcontainers"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_tasks_are_persisted(integration_client):
    """Verifica que múltiplas tarefas são salvas e recuperadas."""
    await integration_client.post("/tasks", json={"title": "Tarefa 1"})
    await integration_client.post("/tasks", json={"title": "Tarefa 2"})

    response = await integration_client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 2
    titles = [t["title"] for t in tasks]
    assert "Tarefa 1" in titles
    assert "Tarefa 2" in titles
