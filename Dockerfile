FROM python:3.14-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_HTTP_TIMEOUT=100 \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
COPY . .
RUN uv sync --no-dev --frozen --no-editable

FROM python:3.14-slim-bookworm AS final
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:${PATH}"

ENTRYPOINT [ "mitmproxy2swagger" ]
