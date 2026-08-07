"""The UCP Server driven the way an Agent drives it: over its HTTP boundary.

Both of the UCP Server's neighbours are stubbed at *their* HTTP boundaries rather
than replaced by fake objects, so what these tests exercise is the real
delegation — the request the UCP Server actually sends to the system of record,
the response shape it actually reads back, and the events a window would actually
see. `tests/test_catalog_over_the_real_stack.py` runs the same journey against
the real Java service to keep the Invoice API stub honest.
"""

import json

import httpx
import pytest
import respx

from ucp_server.app import create_app

INVOICE_API = "http://invoice-api.test"
EVENT_BUS = "http://bus.test"
MERCHANT = "http://merchant.test"

ADAS_KEY = "demo-key-ada"
ADA = "ada@example.com"
GRACES_KEY = "demo-key-grace"
GRACE = "grace@example.com"


class InvoiceApiStub:
    """The Merchant's invoicing system, answering as itself.

    One route answering from a ledger, rather than a route per Payer, so that
    asking for a Payer nobody set up returns an empty list — what the real service
    does — instead of failing to match and looking like a network fault.
    """

    def __init__(self, network):
        self._ledger = {}
        self._answering = True
        network.get(f"{INVOICE_API}/invoices").mock(side_effect=self._answer)

    def holds(self, *invoices, against):
        """Record which Invoices the Merchant holds against one Payer."""
        self._ledger[against] = list(invoices)

    def is_down(self):
        self._answering = False

    def _answer(self, request):
        if not self._answering:
            return httpx.Response(503)
        asked_about = request.url.params.get("payerEmail")
        return httpx.Response(200, json=self._ledger.get(asked_about, []))


@pytest.fixture
def network():
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def invoice_api(network):
    return InvoiceApiStub(network)


@pytest.fixture
def merchant_window(network):
    """Everything the UCP Server published while a test ran."""
    published = []

    def watch(request):
        published.append(json.loads(request.content))
        return httpx.Response(202)

    network.post(f"{EVENT_BUS}/events").mock(side_effect=watch)
    return published


@pytest.fixture
async def client(invoice_api, merchant_window):
    app = create_app(
        invoice_api_url=INVOICE_API,
        event_bus_url=EVENT_BUS,
        api_keys={ADAS_KEY: ADA, GRACES_KEY: GRACE},
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=MERCHANT
    ) as agent:
        yield agent
