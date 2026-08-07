"""The Agent.

The Payer's, running on the Payer's machine, reaching the Merchant only over UCP. It
does nothing until it is woken, and a Wake is the only way in — there is no loop here
polling for work, and no path to payment that does not start at `/agent/wake`.
"""

import contextlib
import os

from demo_events import EventPublisher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.merchant import Merchant
from agent.run import AgentRun
from agent.wakes import InvoiceWatch

SERVICE = "agent"


class Wake(BaseModel):
    """Why the Agent is being woken.

    Carried so the agent window can say what started a run. Every trigger the Agent has
    — Run Agent Now, an Invoice created, a scheduler tick, an Approval granted — enters
    by this one door, differing only in what they write here.
    """

    because: str = "Run Agent Now"


def create_app(
    ucp_server_url: str | None = None,
    event_bus_url: str | None = None,
    api_key: str | None = None,
    watch_for_invoices: bool = True,
) -> FastAPI:
    bus_url = event_bus_url or os.environ.get("EVENT_BUS_URL", "http://event-bus:8100")
    events = EventPublisher(bus_url=bus_url, service=SERVICE)
    merchant = Merchant(
        base_url=ucp_server_url
        or os.environ.get("UCP_SERVER_URL", "http://ucp-server:8000"),
        api_key=api_key or os.environ.get("UCP_API_KEY", ""),
    )
    run = AgentRun(merchant, events)
    watch = InvoiceWatch(bus_url, run)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await events.publish("service.started", payload={"service": SERVICE})
        if watch_for_invoices:
            watch.start()
        yield
        if watch_for_invoices:
            await watch.stop()
        await merchant.aclose()
        await events.aclose()

    app = FastAPI(title="Agent", lifespan=lifespan)

    # The agent window is served from another origin, and Run Agent Now is pressed in a
    # browser. Wide open because in the demo this Agent is the Payer's own process on
    # the Payer's own machine, reachable by nothing else.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "up", "service": SERVICE}

    @app.post("/agent/wake")
    async def wake(wake: Wake = Wake()) -> dict:
        """Run the Agent once.

        Answers when the run is over rather than accepting and running behind the
        caller's back: a run is short, and a demo where the button reports what happened
        is worth more than one where it reports that something will.
        """
        return await run.wake(wake.because)

    @app.post("/demo/ping", status_code=202)
    async def ping(correlation_id: str | None = None) -> dict:
        """Publishes on demand, so a publish can be driven from this service alone."""
        await events.publish("demo.ping", correlation_id=correlation_id)
        return {"published": "demo.ping", "service": SERVICE}

    return app


app = create_app()
