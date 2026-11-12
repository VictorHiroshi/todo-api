from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=120)]
    description: Annotated[str | None, Field(default=None, max_length=1000)] = None
    done: bool = False


class TaskCreate(TaskBase):
    """Payload para criar uma tarefa"""


class TaskUpdate(BaseModel):
    """Payload para atualização parcial — todos os campos opcionais."""

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=120)] = (
        None
    )
    description: Annotated[str | None, Field(default=None, max_length=1000)] = None
    done: bool | None = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
