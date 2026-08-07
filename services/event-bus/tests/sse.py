"""Reading an SSE stream the way a demo window reads it."""

import asyncio
import contextlib
import json


class Stream:
    """An open subscription, buffering events as they arrive."""

    def __init__(self):
        self._events = asyncio.Queue()
        self._heartbeats = asyncio.Queue()

    async def next_event(self, timeout=2.0):
        return await asyncio.wait_for(self._events.get(), timeout)

    async def next_heartbeat(self, timeout=2.0):
        return await asyncio.wait_for(self._heartbeats.get(), timeout)


async def past_the_bus_announcing_itself(stream):
    """Every stream opens with the Event Bus's own arrival. Step over it."""
    first = await stream.next_event()
    assert (first["service"], first["type"]) == ("event-bus", "service.started")
    return stream


@contextlib.asynccontextmanager
async def open_stream(client, path="/events", last_event_id=None, window=None):
    stream = Stream()
    connected = asyncio.Event()
    headers = {"Last-Event-ID": last_event_id} if last_event_id else {}
    params = {"window": window} if window else {}

    async def pump():
        async with client.stream(
            "GET", path, headers=headers, params=params
        ) as response:
            connected.set()
            data = []
            async for line in response.aiter_lines():
                line = line.rstrip("\n")
                if line.startswith(":"):
                    await stream._heartbeats.put(line[1:].strip())
                elif line.startswith("data:"):
                    data.append(line[len("data:") :].lstrip())
                elif line == "" and data:
                    await stream._events.put(json.loads("\n".join(data)))
                    data = []

    pumping = asyncio.create_task(pump())
    await connected.wait()
    try:
        yield stream
    finally:
        pumping.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await pumping
