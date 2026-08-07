# Build context is the repo root: this service is part of a monorepo, and the repo
# layout is mirrored inside the image to match the other services.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /repo/services/event-bus
COPY services/event-bus/pyproject.toml services/event-bus/uv.lock ./
COPY services/event-bus/src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8100
CMD ["uv", "run", "uvicorn", "event_bus.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8100"]
