"""The Wake a human does not perform: an Invoice appearing at the Merchant.

These drive `InvoiceWatch` against a bus that really streams, rather than calling the
run directly, because what is worth testing is the part between the two — that an event
on the wire becomes a Wake, that a burst becomes one run, and that the Agent does not
wake itself by paying.
"""

import asyncio
import json

import httpx
import pytest
import respx

from agent.wakes import InvoiceWatch

BUS = "http://bus.test"


def sse(*events):
    """An Event Bus response, framed the way the real bus frames one."""
    body = "retry: 1000\n\n: heartbeat\n\n"
    for index, event in enumerate(events):
        body += f"id: evt-{index}\ndata: {json.dumps(event)}\n\n"
    return body


class Bus:
    """An Event Bus that streams, to the extent the Agent reads one."""

    def __init__(self):
        self._lines = asyncio.Queue()

    def announce(self, type, service="invoice-api"):
        self._lines.put_nowait(f'data: {{"type": "{type}", "service": "{service}"}}')

    async def lines(self):
        while True:
            yield await self._lines.get()


class RunSpy:
    """A run that records being woken instead of doing anything."""

    def __init__(self):
        self.wakes = []
        self.woken = asyncio.Event()
        self.let_it_finish = asyncio.Event()
        self.let_it_finish.set()

    async def wake(self, because):
        self.wakes.append(because)
        self.woken.set()
        await self.let_it_finish.wait()
        return {}


async def watching(bus, run, monkeypatch):
    """An InvoiceWatch reading the given bus."""
    watch = InvoiceWatch("http://bus.test", run, reconnect_seconds=0.01)

    async def read_stream():
        async for line in bus.lines():
            if line.startswith("data:"):
                import json

                event = json.loads(line[len("data:") :].strip())
                if event.get("type") == "invoice.created":
                    watch._work_to_do.set()

    monkeypatch.setattr(watch, "_read_stream", read_stream)
    watch.start()
    return watch


async def settled():
    """Let the wake loop get as far as it is going to get."""
    for _ in range(10):
        await asyncio.sleep(0)


async def test_an_invoice_created_on_the_real_stream_wakes_the_agent():
    """The Agent's own SSE reading, over a bus answering as the real one does."""
    run = RunSpy()
    watch = InvoiceWatch(BUS, run)
    with respx.mock:
        respx.get(f"{BUS}/events").mock(
            return_value=httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                text=sse(
                    {"type": "service.started", "service": "invoice-api"},
                    {"type": "invoice.created", "service": "invoice-api"},
                ),
            )
        )

        await watch._read_stream()

    assert watch._work_to_do.is_set()


@pytest.mark.parametrize(
    "event",
    [
        {"type": "invoice.paid", "service": "invoice-api"},
        {"type": "ucp.checkout_completed", "service": "ucp-server"},
        {"type": "agent.finished", "service": "agent"},
    ],
)
async def test_the_agents_own_payments_do_not_wake_it_again(event):
    """Waking on a payment would be a loop with a payment in it."""
    run = RunSpy()
    watch = InvoiceWatch(BUS, run)
    with respx.mock:
        respx.get(f"{BUS}/events").mock(
            return_value=httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                text=sse(event),
            )
        )

        await watch._read_stream()

    assert not watch._work_to_do.is_set()


async def test_a_burst_of_invoices_is_one_run_not_several(monkeypatch):
    bus, run = Bus(), RunSpy()
    # Hold the first run open so the burst arrives while it is still going.
    run.let_it_finish.clear()
    watch = await watching(bus, run, monkeypatch)

    bus.announce("invoice.created")
    await asyncio.wait_for(run.woken.wait(), timeout=2)
    for _ in range(5):
        bus.announce("invoice.created")
    await settled()
    run.let_it_finish.set()
    await settled()

    # A run pays everything it finds outstanding, so five Invoices raised during one
    # run are one more run's worth of work — not five.
    assert run.wakes == ["an Invoice was created"] * 2
    await watch.stop()


async def test_a_run_that_fails_does_not_stop_the_next_invoice_waking_the_agent(
    monkeypatch,
):
    bus = Bus()

    class FailingRun(RunSpy):
        async def wake(self, because):
            await super().wake(because)
            raise RuntimeError("the Merchant fell over")

    run = FailingRun()
    watch = await watching(bus, run, monkeypatch)

    bus.announce("invoice.created")
    await asyncio.wait_for(run.woken.wait(), timeout=2)
    run.woken.clear()
    bus.announce("invoice.created")
    await asyncio.wait_for(run.woken.wait(), timeout=2)

    assert len(run.wakes) == 2
    await watch.stop()
