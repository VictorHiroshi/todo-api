import uuid

import structlog
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from todo_api.config import get_settings
from todo_api.logging_config import configure_logging
from todo_api.routers import auth, health, tasks

settings = get_settings()
logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=str(uuid.uuid4()),
            path=request.url.path,
            method=request.method,
        )
        response = await call_next(request)
        structlog.contextvars.bind_contextvars(status_code=response.status_code)
        logger.info("request_completed")  # já inclui request_id, path, status
        return response


app = FastAPI(
    title="Todo API",
    version="0.1.0",
    description="API de tarefas para revisão de FastAPI + Pydantic + SQLAlchemy async + Alembic.",
)

configure_logging(debug=settings.debug)
app.add_middleware(RequestContextMiddleware)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(tasks.router)
