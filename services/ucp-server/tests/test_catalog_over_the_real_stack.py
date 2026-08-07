"""One journey, run against the real demo rather than a stub of it.

The rest of this suite stubs the Invoice API, which makes it fast and makes it
possible to describe awkward states — but every one of those stubs is a
hand-written guess at what a Java service returns. This test is what makes the
guess checkable: it raises a real Invoice on the real system of record and then
finds it through the real Catalog, so a field renamed on either side fails here.

    docker compose up --build --wait
    uv run pytest -m integration

The fixture will bring the stack up itself if it is not already running.
"""

import asyncio
import contextlib
import json
import subprocess
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.integration

COMPOSE_FILE = Path(__file__).resolve().parents[3] / "compose.yaml"
INVOICE_API = "http://localhost:8080"
UCP_SERVER = "http://localhost:8000"
EVENT_BUS = "http://localhost:8100"

# Configured on both services in compose.yaml.
AGENTS_API_KEY = "demo-agent-key"
THE_PAYER = "vampserv@gmail.com"

EXTENSION = "com.lapins.demo.invoicing.invoice"


@pytest.fixture(scope="session")
def demo():
    """The whole demo, brought up the way an operator brings it up."""
    subprocess.run(
        ["docker", "compose", "--file", str(COMPOSE_FILE), "up", "--build", "--wait"],
        check=True,
        timeout=900,
    )


@pytest.fixture
async def merchant(demo):
    async with httpx.AsyncClient(base_url=INVOICE_API, timeout=30) as client:
        yield client


@pytest.fixture
async def agent(demo):
    async with httpx.AsyncClient(timeout=30) as client:
        yield client


@contextlib.asynccontextmanager
async def merchant_window(demo):
    """A live subscription to exactly what the merchant window is shown."""
    arriving = asyncio.Queue()

    async def watch():
        async with httpx.AsyncClient(timeout=None) as window:
            async with window.stream(
                "GET", f"{EVENT_BUS}/events", params={"window": "merchant"}
            ) as stream:
                watching.set()
                async for line in stream.aiter_lines():
                    if line.startswith("data:"):
                        await arriving.put(json.loads(line[len("data:") :].strip()))

    watching = asyncio.Event()
    watcher = asyncio.create_task(watch())
    await watching.wait()
    try:
        yield arriving
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await watcher


async def until_seen(arriving, type, within=15.0):
    """Wait for one kind of event, stepping over whatever else is happening."""

    async def wait():
        while True:
            event = await arriving.get()
            if event["type"] == type:
                return event

    return await asyncio.wait_for(wait(), within)


async def test_an_agent_discovers_the_merchant_and_finds_an_invoice_just_raised(
    merchant, agent
):
    raised = await merchant.post(
        "/invoices",
        json={
            "payerEmail": THE_PAYER,
            "originalTotalMinorUnits": 43000,
            "currency": "USD",
            "dueDate": "2026-09-30",
            "allowedPaymentMethods": ["BANK", "CARD"],
        },
    )
    raised.raise_for_status()
    doc_number = raised.json()["docNumber"]

    # Nothing below is told where to look: the endpoint comes out of the profile,
    # which is the whole point of publishing one.
    profile = (await agent.get(f"{UCP_SERVER}/.well-known/ucp")).json()["ucp"]
    endpoint = next(
        service
        for service in profile["services"]["dev.ucp.shopping"]
        if service["transport"] == "rest"
    )["endpoint"]
    assert profile["capabilities"][EXTENSION][0]["extends"] in profile["capabilities"]

    found = await agent.post(
        f"{endpoint}/catalog/search",
        json={"query": "outstanding invoices"},
        headers={"X-API-Key": AGENTS_API_KEY},
    )
    found.raise_for_status()

    invoices = {
        product[EXTENSION]["doc_number"]: product[EXTENSION]
        for product in found.json()["products"]
    }
    assert doc_number in invoices
    assert invoices[doc_number]["balance_due"] == {"amount": 43000, "currency": "USD"}
    assert invoices[doc_number]["due_date"] == "2026-09-30"
    assert invoices[doc_number]["payer"] == {"email": THE_PAYER}
    assert invoices[doc_number]["merchant"]["name"] == "Ed's Surf Shop"
    assert invoices[doc_number]["allowed_payment_methods"] == ["BANK", "CARD"]


async def test_the_merchant_window_watches_the_ucp_layer_answer_the_agent(demo, agent):
    async with merchant_window(demo) as arriving:
        answered = await agent.post(
            f"{UCP_SERVER}/catalog/search",
            json={"query": "outstanding invoices"},
            headers={"X-API-Key": AGENTS_API_KEY},
        )
        answered.raise_for_status()

        searched = await until_seen(arriving, "ucp.catalog_searched")

    # The merchant window carries both servers' activity. The label is what lets an
    # operator tell the exposure layer's behaviour from the system of record's.
    assert searched["service"] == "ucp-server"
