"""The Agent driven the way a human drives it: by waking it over its HTTP boundary.

The Merchant is stubbed at *its* HTTP boundary rather than replaced by a fake object, so
what these tests exercise is the real conversation — the Discovery Profile the Agent
actually reads, the requests it actually sends, and the events the agent window would
actually see.
"""

import json

import httpx
import pytest
import respx

from agent.app import create_app

UCP_SERVER = "http://ucp-server.test"
EVENT_BUS = "http://bus.test"
AGENT = "http://agent.test"
API_KEY = "demo-agent-key"

EXTENSION = "com.lapins.demo.invoicing.invoice"


class MerchantStub:
    """A UCP Merchant whose catalogue is Invoices, answering as itself."""

    def __init__(self, network):
        self._invoices = {}
        self._checkouts = {}
        self._capabilities = [
            "dev.ucp.shopping.catalog.search",
            "dev.ucp.shopping.checkout",
            EXTENSION,
        ]
        network.get(f"{UCP_SERVER}/.well-known/ucp").mock(side_effect=self._profile)
        network.post(f"{UCP_SERVER}/catalog/search").mock(side_effect=self._search)
        network.post(f"{UCP_SERVER}/checkout").mock(side_effect=self._open_checkout)
        network.post(
            url__regex=rf"{UCP_SERVER}/checkout/(?P<checkout_id>[^/]+)/complete"
        ).mock(side_effect=self._complete)

    def holds(self, invoice_id, doc_number="kIV88PDO", balance_due=12500, due_date="2026-08-14"):
        self._invoices[invoice_id] = {
            "id": invoice_id,
            "doc_number": doc_number,
            "balance_due": balance_due,
            "due_date": due_date,
        }

    def offers_only(self, *capabilities):
        self._capabilities = list(capabilities)

    def _profile(self, request):
        return httpx.Response(
            200,
            json={
                "ucp": {
                    "version": "2026-04-08",
                    "services": {
                        "dev.ucp.shopping": [
                            {"transport": "rest", "endpoint": UCP_SERVER}
                        ]
                    },
                    "capabilities": {
                        name: [{"version": "2026-04-08"}]
                        for name in self._capabilities
                    },
                },
            },
        )

    def _search(self, request):
        return httpx.Response(
            200,
            json={
                "products": [
                    {
                        "id": invoice["id"],
                        "title": f"Invoice {invoice['doc_number']}",
                        EXTENSION: {
                            "doc_number": invoice["doc_number"],
                            "due_date": invoice["due_date"],
                            "balance_due": {
                                "amount": invoice["balance_due"],
                                "currency": "USD",
                            },
                            "outstanding": True,
                            "overdue": False,
                        },
                    }
                    for invoice in self._invoices.values()
                ]
            },
        )

    def _open_checkout(self, request):
        asked = json.loads(request.content)
        invoice_ids = [line["item"]["id"] for line in asked["line_items"]]
        checkout_id = f"chk-{len(self._checkouts) + 1}"
        self._checkouts[checkout_id] = invoice_ids
        return httpx.Response(
            201, json=self._as_checkout(checkout_id, invoice_ids, "ready_for_complete")
        )

    def _complete(self, request, checkout_id):
        invoice_ids = self._checkouts[checkout_id]
        settled = self._as_checkout(checkout_id, invoice_ids, "completed")
        # The Invoices leave the catalogue, exactly as they do when the real Merchant
        # settles them — so an Agent that verifies by re-reading learns something.
        for invoice_id in invoice_ids:
            self._invoices.pop(invoice_id, None)
        return httpx.Response(200, json=settled)

    def _as_checkout(self, checkout_id, invoice_ids, status):
        total = sum(self._invoices[id]["balance_due"] for id in invoice_ids)
        return {
            "id": checkout_id,
            "status": status,
            "currency": "USD",
            "line_items": [
                {
                    "id": invoice_id,
                    "item": {"id": invoice_id, "price": self._invoices[invoice_id]["balance_due"]},
                    "quantity": 1,
                }
                for invoice_id in invoice_ids
            ],
            "totals": [
                {"type": "subtotal", "amount": total},
                {"type": "total", "amount": total},
            ],
        }


@pytest.fixture
def network():
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def merchant(network):
    return MerchantStub(network)


@pytest.fixture
def agent_window(network):
    """Everything the Agent published while a test ran."""
    published = []

    def watch(request):
        published.append(json.loads(request.content))
        return httpx.Response(202)

    network.post(f"{EVENT_BUS}/events").mock(side_effect=watch)
    return published


@pytest.fixture
async def client(merchant, agent_window):
    app = create_app(
        ucp_server_url=UCP_SERVER, event_bus_url=EVENT_BUS, api_key=API_KEY
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=AGENT
    ) as human:
        yield human
