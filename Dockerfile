FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_HTTP_TIMEOUT=100 \
    UV_NO_CACHE=1
WORKDIR /app
RUN uv pip install --system poetry poetry-plugin-export
COPY pyproject.toml poetry.lock ./
RUN uv venv /venv && \
    poetry export -f requirements.txt -o requirements.txt && \
    VIRTUAL_ENV=/venv uv pip install -r requirements.txt
COPY . .
RUN poetry build && \
    VIRTUAL_ENV=/venv uv pip install dist/*.whl

FROM python:3.12-slim-bookworm AS final
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:${PATH}"

ENTRYPOINT [ "mitmproxy2swagger" ]
