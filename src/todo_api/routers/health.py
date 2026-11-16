from fastapi import APIRouter

from todo_api.config import get_settings

router = APIRouter(tags=["infra"])
settings = get_settings()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
