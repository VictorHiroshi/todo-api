from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from todo_api.config import get_settings

# pwdlib: usa Argon2 por padrão (recomendado atualmente)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Gera o hash Argon2 da senha para armazenar no banco."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash armazenado."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Cria um JWT assinado com HS256.
    O subject (sub) é o identificador do usuário (ex.: email ou id).
    """
    settings = get_settings()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decodifica e valida o JWT.
    Retorna o payload se válido, ou None se o token for inválido/expirado.
    """
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},  # exige que sub e exp existam
        )
    except jwt.PyJWTError:
        return None
