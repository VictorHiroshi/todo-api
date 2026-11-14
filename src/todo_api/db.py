from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from todo_api.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""


settings = get_settings()
_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # loga SQL em dev
    pool_pre_ping=True,  # verifica conexões mortas
)
_SessionFactory = async_sessionmaker(
    _engine,
    expire_on_commit=False,  # ESSENCIAL para FastAPI async
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _SessionFactory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
