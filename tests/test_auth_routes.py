import pytest


@pytest.mark.asyncio
async def test_register_creates_user(client):
    response = await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "senha12345"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # nunca vaza


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "senha12345"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    response = await client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_token(client):
    await client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "senha12345"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "senha12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "senha12345"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "errada"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client):
    response = await client.get("/tasks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client):
    # Registra e faz login
    await client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "senha12345"},
    )
    login = await client.post(
        "/auth/login",
        data={"username": "auth@example.com", "password": "senha12345"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_token(client):
    response = await client.get(
        "/tasks",
        headers={"Authorization": "Bearer token.invalido.aqui"},
    )
    assert response.status_code == 401
