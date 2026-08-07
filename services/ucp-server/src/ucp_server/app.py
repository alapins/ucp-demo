"""The UCP Server: the Merchant's Invoices, exposed over UCP.

An exposure layer and nothing more. Every Invoice fact on the way out came from
the Invoice API on the way in, so the Merchant remains the sole system of record
and this server can be changed or removed without risking Invoice state.
"""

import contextlib
import os

from demo_events import EventPublisher
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ucp_server import config
from ucp_server.exceptions import UcpError
from ucp_server.invoice_api import InvoiceApi
from ucp_server.payers import Payers
from ucp_server.routes.catalog import catalog_router
from ucp_server.routes.checkout import checkout_router
from ucp_server.routes.discovery import router as discovery_router
from ucp_server.routes.invoice_extension import router as invoice_extension_router
from ucp_server.services.catalog_service import CatalogService
from ucp_server.services.invoice_checkout import InvoiceCheckout

SERVICE = "ucp-server"


def create_app(
    invoice_api_url: str | None = None,
    event_bus_url: str | None = None,
    api_keys: dict[str, str] | None = None,
) -> FastAPI:
    events = EventPublisher(
        bus_url=event_bus_url
        or os.environ.get("EVENT_BUS_URL", "http://event-bus:8100"),
        service=SERVICE,
    )
    invoice_api = InvoiceApi(
        base_url=invoice_api_url
        or os.environ.get("INVOICE_API_URL", "http://invoice-api:8080")
    )
    payers = Payers(api_keys) if api_keys is not None else Payers.from_environment()

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await events.publish("service.started", payload={"service": SERVICE})
        yield
        await invoice_api.aclose()
        await events.aclose()

    app = FastAPI(
        title="UCP Server",
        version=config.get_server_version(),
        lifespan=lifespan,
    )

    @app.exception_handler(UcpError)
    async def ucp_exception_handler(request: Request, exc: UcpError):
        """Report a failure in the UCP envelope, as the reference server does."""
        del request  # Unused.
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ucp": {"version": config.get_server_version(), "status": "error"},
                "messages": [
                    {
                        "type": "error",
                        "code": exc.code,
                        "content": exc.message,
                        "severity": exc.severity,
                    }
                ],
            },
        )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "up", "service": SERVICE}

    @app.post("/demo/ping", status_code=202)
    async def ping(correlation_id: str | None = None) -> dict:
        """Publishes on demand, so a publish can be driven from this service alone.

        Walking-skeleton scaffolding, kept because the Invoice API and the Agent
        still carry theirs. Now that this server publishes real activity, all three
        can go together.
        """
        await events.publish("demo.ping", correlation_id=correlation_id)
        return {"published": "demo.ping", "service": SERVICE}

    app.include_router(discovery_router)
    app.include_router(invoice_extension_router)
    app.include_router(catalog_router(CatalogService(invoice_api, events), payers))
    app.include_router(checkout_router(InvoiceCheckout(invoice_api, events), payers))

    return app


app = create_app()
