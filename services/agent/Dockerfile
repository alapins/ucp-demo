# Build context is the repo root: this service shares packages/demo-events.
# The repo layout is mirrored inside the image so the path dependency in
# pyproject.toml resolves exactly as it does on a developer's machine.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

COPY packages/demo-events /repo/packages/demo-events

WORKDIR /repo/services/agent
COPY services/agent/pyproject.toml services/agent/uv.lock ./
COPY services/agent/src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8200
CMD ["uv", "run", "uvicorn", "agent.app:app", "--host", "0.0.0.0", "--port", "8200"]
