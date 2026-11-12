from fastapi import FastAPI

from todo_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Todo API",
    version="0.1.0",
    description="API de tarefas para revisão de FastAPI + Pydantic + SQLAlchemy async + Alembic.",
)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
