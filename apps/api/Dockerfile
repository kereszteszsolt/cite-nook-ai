FROM ghcr.io/astral-sh/uv:0.11.29-python3.14-trixie-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/uv.lock ./uv.lock
COPY apps/api/app ./app
COPY packages/brand/brand.json /config/brand.json

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime-base AS runtime-llamaindex

RUN uv sync --frozen --no-dev --no-editable --extra llamaindex

FROM runtime-base AS runtime-native

RUN uv sync --frozen --no-dev --no-editable
