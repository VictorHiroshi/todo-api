from datetime import datetime
from typing import Annotated, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TaskBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=120)]
    description: Annotated[str | None, Field(default=None, max_length=1000)] = None
    done: bool = False


class TaskCreate(TaskBase):
    """Payload para criar uma tarefa"""


class TaskUpdate(BaseModel):
    """Payload para atualização parcial — todos os campos opcionais."""

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=120)] = None
    description: Annotated[str | None, Field(default=None, max_length=1000)] = None
    done: bool | None = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class CursorPage[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    """Payload de registro. A senha nunca é retornada."""

    password: Annotated[str, Field(min_length=8, max_length=72)]


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
