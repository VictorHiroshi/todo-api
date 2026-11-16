import os

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Usa Redis se disponível, senão memória local
redis_url = os.getenv("REDIS_URL")
limiter = Limiter(
    key_func=get_remote_address,  # por IP; para usuário, veja abaixo
    storage_uri=redis_url,
    default_limits=["100/minute"],
)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Handler customizado para 429 com mensagem clara."""
    # Narrowing seguro: o SlowAPI só chama este handler para RateLimitExceeded
    detail = exc.detail if isinstance(exc, RateLimitExceeded) else "Muitas requisições."
    return Response(
        content=f'{{"detail": "{detail}"}}',
        status_code=429,
        media_type="application/json",
    )
