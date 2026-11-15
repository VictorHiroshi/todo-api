import base64
import binascii
import json
from datetime import datetime
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, Path, Query, status
from sqlalchemy import func, select

from todo_api.config import get_settings
from todo_api.db import SessionDep
from todo_api.models import Task
from todo_api.schemas import CursorPage, Page, TaskCreate, TaskResponse, TaskUpdate

settings = get_settings()

app = FastAPI(
    title="Todo API",
    version="0.1.0",
    description="API de tarefas para revisão de FastAPI + Pydantic + SQLAlchemy async + Alembic.",
)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task(payload: TaskCreate, session: SessionDep) -> Task:
    task = Task(**payload.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)  # carrega id, created_at, updated_at do banco
    return task


@app.get(
    "/tasks",
    response_model=Page[TaskResponse],
    status_code=status.HTTP_200_OK,
    tags=["tasks"],
)
async def list_tasks(
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(default=0, ge=0, description="Itens a pular"),
) -> Page[TaskResponse]:
    # 1. Total de registros (para o cliente saber quantas páginas existem)
    total = await session.scalar(select(func.count()).select_from(Task))

    # 2. Busca paginada e ordenada
    stmt = select(Task).order_by(Task.created_at.desc(), Task.id.desc()).limit(limit).offset(offset)
    result = await session.scalars(stmt)
    tasks = result.all()

    return Page[TaskResponse](
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


def _encode_cursor(created_at: datetime, task_id: int) -> str:
    payload = {"created_at": created_at.isoformat(), "id": task_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw.decode("utf-8"))
        return int(data["id"])
    except binascii.Error, UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError, TypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cursor inválido",
        )


@app.get("/tasks/cursor", response_model=CursorPage[TaskResponse], tags=["tasks"])
async def list_tasks_cursor(
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=100),
    cursor: str | None = Query(default=None, description="Cursor da página anterior"),
) -> CursorPage[TaskResponse]:
    stmt = select(Task).order_by(Task.id.desc()).limit(limit + 1)

    if cursor:
        last_id = _decode_cursor(cursor)
        stmt = stmt.where(Task.id < last_id)

    result = await session.scalars(stmt)
    tasks = list(result.all())

    has_more = len(tasks) > limit
    if has_more:
        tasks = tasks[:limit]

    next_cursor = None
    if has_more and tasks:
        last = tasks[-1]
        next_cursor = _encode_cursor(last.created_at, last.id)

    return CursorPage[TaskResponse](
        items=[TaskResponse.model_validate(t) for t in tasks],
        next_cursor=next_cursor,
    )


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    tags=["tasks"],
)
async def get_task(session: SessionDep, task_id: int = Path(description="ID da tarefa")) -> TaskResponse:
    stmt = select(Task).where(Task.id == task_id)
    result = await session.scalar(stmt)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")
    return TaskResponse.model_validate(result)


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    tags=["tasks"],
)
async def update_task(
    session: SessionDep,
    task_data: Annotated[TaskUpdate, Body()],
    task_id: int = Path(description="ID da tarefa"),
) -> TaskResponse:
    stmt = select(Task).where(Task.id == task_id)
    result = await session.scalar(stmt)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(result, key, value)
    await session.commit()
    await session.refresh(result)
    return TaskResponse.model_validate(result)


@app.delete(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    tags=["tasks"],
)
async def delete_task(
    session: SessionDep,
    task_id: int = Path(description="ID da tarefa"),
) -> TaskResponse:
    stmt = select(Task).where(Task.id == task_id)
    result = await session.scalar(stmt)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")
    await session.delete(result)
    await session.commit()
    return TaskResponse.model_validate(result)
