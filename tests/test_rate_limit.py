import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address

import todo_api.main as main_module


@pytest.mark.asyncio
async def test_rate_limit_returns_429(authenticated_client, monkeypatch):
    # Faz requisições acima do limite (ex.: 11 para um limite de 10/min)
    test_limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
    monkeypatch.setattr(main_module, "limiter", test_limiter)

    for _ in range(12):
        response = await authenticated_client.post("/tasks", json={"title": "teste"})
    assert response.status_code == 429
