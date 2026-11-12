import pytest
from pydantic import ValidationError

from todo_api.config import Settings


def test_settings_reads_from_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings(_env_file=None)
    assert settings.database_url == "postgresql+asyncpg://test:test@localhost:5432/testdb"
    assert settings.app_env == "staging"
    assert settings.debug is True


def test_settings_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
