import asyncio
import contextlib
import socket

import httpx
import pytest
import uvicorn

from event_bus.app import create_app


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
async def bus():
    """Starts an Event Bus on a loopback port and returns a client pointed at it.

    Real HTTP rather than an in-process ASGI transport: the seam under test is the
    Event Bus's HTTP boundary, and an SSE stream never ends, so it cannot be read
    through a transport that buffers whole response bodies.
    """
    running = []

    async def start(**settings) -> httpx.AsyncClient:
        port = _free_port()
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(**settings),
                host="127.0.0.1",
                port=port,
                log_level="warning",
            )
        )
        serving = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.01)
        client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}")
        running.append((server, serving, client))
        return client

    yield start

    for server, serving, client in running:
        await client.aclose()
        server.should_exit = True
        with contextlib.suppress(asyncio.CancelledError, TimeoutError):
            await asyncio.wait_for(serving, timeout=5)


@pytest.fixture
async def client(bus):
    return await bus()
