FROM python:3.15-slim

WORKDIR /app

# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copia dependências primeiro (cache layer)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copia o código
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

RUN uv sync --frozen --no-dev

# Adiciona src ao PYTHONPATH para o uvicorn encontrar todo_api
ENV PYTHONPATH=/app/src

CMD ["uv", "run", "uvicorn", "todo_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
