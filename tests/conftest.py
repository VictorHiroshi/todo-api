import pytest
import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from todo_api.db import Base, get_session
from todo_api.main import app

# Banco de teste em memória
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Cria o schema e fornece uma sessão limpa para cada teste."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """Sobrescreve a dependência get_session para usar o banco de teste."""

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------- Fixture do container PostgreSQL (session-scoped) ----------
@pytest.fixture(scope="session")
def postgres_container():
    """Sobe um PostgreSQL descartável para os testes de integração."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def postgres_engine(postgres_container):
    """Cria a engine async apontando para o container."""
    url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# ---------- Fixture de sessão do banco (function-scoped, com rollback) ----------
@pytest_asyncio.fixture(loop_scope="session")
async def integration_session(postgres_engine):
    """
    Fornece uma sessão que sempre faz rollback no final.
    Assim, cada teste começa com o banco limpo.
    """
    async with postgres_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_factory() as session:
            yield session
        await transaction.rollback()


# ---------- Cliente HTTP para testes de integração ----------
@pytest_asyncio.fixture(loop_scope="session")
async def integration_client(integration_session: AsyncSession):
    """Cliente que usa a sessão do Postgres real (com rollback)."""

    async def override_get_session():
        yield integration_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
