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


@pytest.mark.asyncio
async def test_list_tasks_empty(client):
    response = await client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "total": 0, "limit": 10, "offset": 0}


@pytest.mark.asyncio
async def test_list_tasks_with_pagination(client):
    # Cria 3 tarefas
    for i in range(3):
        await client.post("/tasks", json={"title": f"Tarefa {i}"})

    # Primeira página
    response = await client.get("/tasks?limit=2&offset=0")
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2
    # Ordem descendente por created_at/id
    assert data["items"][0]["title"] == "Tarefa 2"

    # Segunda página
    response = await client.get("/tasks?limit=2&offset=2")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Tarefa 0"


@pytest.mark.asyncio
async def test_list_tasks_rejects_invalid_limit(client):
    response = await client.get("/tasks?limit=0")
    assert response.status_code == 422

    response = await client.get("/tasks?limit=101")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_rejects_negative_offset(client):
    response = await client.get("/tasks?offset=-1")
    assert response.status_code == 422


async def _create_tasks(client, n: int) -> list[dict]:
    """Helper: cria N tarefas e retorna a lista de respostas."""
    created = []
    for i in range(n):
        r = await client.post("/tasks", json={"title": f"Tarefa {i}"})
        assert r.status_code == 201
        created.append(r.json())
    return created


@pytest.mark.asyncio
async def test_cursor_empty(client):
    response = await client.get("/tasks/cursor")
    assert response.status_code == 200
    data = response.json()
    assert data == {"items": [], "next_cursor": None}


@pytest.mark.asyncio
async def test_cursor_first_page_returns_limit_plus_one_check(client):
    """Com 3 tarefas e limit=2, a primeira página deve ter 2 itens e next_cursor != None."""
    await _create_tasks(client, 3)

    response = await client.get("/tasks/cursor?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_cursor_pagination_walks_all_items(client):
    """Percorre todas as páginas e verifica que nenhum item é repetido ou perdido."""
    created = await _create_tasks(client, 5)
    expected_titles = {t["title"] for t in created}

    seen_titles: set[str] = set()
    cursor = None
    pages = 0

    while True:
        url = "/tasks/cursor?limit=2"
        if cursor:
            url += f"&cursor={cursor}"
        response = await client.get(url)
        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["title"] not in seen_titles, "Item duplicado entre páginas"
            seen_titles.add(item["title"])

        pages += 1
        cursor = data["next_cursor"]
        if cursor is None:
            break
        assert pages < 10, "Loop infinito — cursor não está avançando"

    assert seen_titles == expected_titles
    assert pages == 3  # 5 itens / limit=2 → 3 páginas (2+2+1)


@pytest.mark.asyncio
async def test_cursor_last_page_has_no_next_cursor(client):
    """A última página deve retornar next_cursor=None."""
    await _create_tasks(client, 2)

    response = await client.get("/tasks/cursor?limit=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_cursor_is_stable_under_inserts(client):
    """
    O teste que diferencia cursor de offset:
    inserir um item novo entre páginas NÃO deve causar duplicata.
    """
    await _create_tasks(client, 3)

    # Página 1
    r1 = await client.get("/tasks/cursor?limit=2")
    page1 = r1.json()
    page1_ids = {i["id"] for i in page1["items"]}
    assert len(page1_ids) == 2

    # Insere uma tarefa nova (que apareceria no topo da ordenação desc)
    await client.post("/tasks", json={"title": "Intrusa"})

    # Página 2 usando o cursor da página 1
    r2 = await client.get(f"/tasks/cursor?limit=2&cursor={page1['next_cursor']}")
    page2 = r2.json()
    page2_ids = {i["id"] for i in page2["items"]}

    # Nenhum item da página 1 deve reaparecer na página 2
    assert page1_ids.isdisjoint(page2_ids), "Cursor retornou item já visto"


@pytest.mark.asyncio
async def test_cursor_rejects_invalid_limit(client):
    response = await client.get("/tasks/cursor?limit=0")
    assert response.status_code == 422

    response = await client.get("/tasks/cursor?limit=101")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cursor_rejects_malformed_cursor(client):
    """Cursor inválido deve retornar erro claro, não 500."""
    response = await client.get("/tasks/cursor?cursor=not-a-valid-cursor")
    # A implementação atual lança exceção no _decode_cursor.
    # Se você ainda não tratou, este teste documenta o comportamento atual.
    assert response.status_code == 400
    assert response.json()["detail"] == "Cursor inválido"


@pytest.mark.asyncio
async def test_cursor_rejects_valid_base64_but_invalid_json(client):
    """Base64 válido, mas conteúdo não é JSON."""
    import base64

    invalid = base64.urlsafe_b64encode(b"not json").decode()
    response = await client.get(f"/tasks/cursor?cursor={invalid}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cursor_rejects_json_without_id(client):
    """JSON válido, mas sem a chave 'id'."""
    import base64
    import json

    payload = base64.urlsafe_b64encode(json.dumps({"foo": 1}).encode()).decode()
    response = await client.get(f"/tasks/cursor?cursor={payload}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_task_returns_task(client):
    created = await client.post("/tasks", json={"title": "Tarefa individual"})
    assert created.status_code == 201

    response = await client.get("/tasks/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Tarefa individual"
    assert data["done"] is False


@pytest.mark.asyncio
async def test_get_task_returns_404_for_missing_id(client):
    response = await client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {"title": "Depois", "description": "Descrição atualizada", "done": True},
            {"title": "Depois", "description": "Descrição atualizada", "done": True},
        ),
        (
            {"title": "Título atualizado"},
            {"title": "Título atualizado", "description": "Descrição original", "done": False},
        ),
        (
            {"description": "Descrição atualizada"},
            {"title": "Antes", "description": "Descrição atualizada", "done": False},
        ),
        (
            {"done": True},
            {"title": "Antes", "description": "Descrição original", "done": True},
        ),
    ],
)
async def test_update_task_updates_fields(client, payload, expected):
    created = await client.post(
        "/tasks",
        json={"title": "Antes", "description": "Descrição original"},
    )
    assert created.status_code == 201

    response = await client.put("/tasks/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == expected["title"]
    assert data["description"] == expected["description"]
    assert data["done"] is expected["done"]

    missing = await client.put("/tasks/999", json=payload)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Tarefa não encontrada"


@pytest.mark.asyncio
async def test_delete_task_removes_task(client):
    created = await client.post("/tasks", json={"title": "Para deletar"})
    assert created.status_code == 201

    response = await client.delete("/tasks/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Para deletar"

    missing = await client.get("/tasks/1")
    assert missing.status_code == 404
