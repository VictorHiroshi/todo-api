from fastapi import FastAPI, status

from todo_api.config import get_settings
from todo_api.db import SessionDep
from todo_api.models import Task
from todo_api.schemas import TaskCreate, TaskResponse

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
