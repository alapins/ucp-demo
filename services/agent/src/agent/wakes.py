"""Waking the Agent when an Invoice is created.

The Agent learns that an Invoice exists by watching the Event Bus. In production it
would not: the bus is the Merchant's, and a Payer's Agent has no place on it — the
notification would arrive as a webhook the Payer registered, or an email, or a poll of
the Catalog on a schedule. ADR 0004 already concedes this compromise in the other
direction, where the Agent *publishes* to the Merchant's bus so that one screen can tell
the whole story. This is the same compromise, and it is confined to this module so that
replacing it means replacing one class.

What is not a compromise is where the wake goes. Nothing here decides anything or talks
to the Merchant; it converts a notification into the same Wake the button raises, and
everything after that is the ordinary run.
"""

import asyncio
import contextlib
import json
import logging

import httpx

logger = logging.getLogger(__name__)

# The one event that means there is new work. Not invoice.paid, which the Agent's own
# payments cause — waking on that would be a loop with a payment in it.
MEANS_NEW_WORK = "invoice.created"

BECAUSE = "an Invoice was created"


class InvoiceWatch:
    """Turns Invoices appearing at the Merchant into Wakes."""

    def __init__(self, bus_url: str, run, reconnect_seconds: float = 1.0):
        self._bus_url = bus_url
        self._run = run
        self._reconnect_seconds = reconnect_seconds
        # A flag rather than a queue of events, because a run pays everything it finds
        # outstanding. Ten Invoices raised at once are one run's worth of work, and the
        # backlog the bus replays when this connects is one run's worth too.
        self._work_to_do = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._listen(), name="agent-invoice-watch"),
            asyncio.create_task(self._work(), name="agent-wake-loop"),
        ]

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks = []

    async def _listen(self) -> None:
        """Watch the bus, reconnecting for as long as the Agent is running."""
        while True:
            try:
                await self._read_stream()
            except asyncio.CancelledError:
                raise
            except Exception as dropped:
                # A bus that is down must not take the Agent with it: Run Agent Now has
                # to keep working, and this connection has to come back on its own.
                logger.warning("the Event Bus connection dropped: %s", dropped)
            await asyncio.sleep(self._reconnect_seconds)

    async def _read_stream(self) -> None:
        async with httpx.AsyncClient(base_url=self._bus_url, timeout=None) as bus:
            async with bus.stream("GET", "/events") as stream:
                stream.raise_for_status()
                async for line in stream.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[len("data:") :].strip())
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == MEANS_NEW_WORK:
                        self._work_to_do.set()

    async def _work(self) -> None:
        """Run the Agent whenever there is work, one run at a time.

        Cleared before the run rather than after, so an Invoice raised while a run is
        in flight is not swallowed by the run that was already going when it arrived.
        """
        while True:
            await self._work_to_do.wait()
            self._work_to_do.clear()
            try:
                await self._run.wake(BECAUSE)
            except asyncio.CancelledError:
                raise
            except Exception as failed:
                # The next Invoice must still wake this Agent.
                logger.exception("the run failed: %s", failed)
