"""The Agent.

A walking skeleton: it holds a place in the topology and proves it can reach the
Event Bus. Wakes, Skills, the Policy Engine, and the decision store arrive in
later tickets.
"""

import contextlib
import os

from demo_events import EventPublisher
from fastapi import FastAPI

SERVICE = "agent"


def create_app() -> FastAPI:
    events = EventPublisher(
        bus_url=os.environ.get("EVENT_BUS_URL", "http://event-bus:8100"),
        service=SERVICE,
    )

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await events.publish("service.started", payload={"service": SERVICE})
        yield
        await events.aclose()

    app = FastAPI(title="Agent", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "up", "service": SERVICE}

    @app.post("/demo/ping", status_code=202)
    async def ping(correlation_id: str | None = None) -> dict:
        """Publishes on demand, so a publish can be driven from this service alone."""
        await events.publish("demo.ping", correlation_id=correlation_id)
        return {"published": "demo.ping", "service": SERVICE}

    return app


app = create_app()
