"""The Event Bus: any demo service publishes here, both windows read from here."""

import asyncio
from collections import deque

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from event_bus.events import Event, Publication

SERVICE = "event-bus"
RECONNECT_AFTER_MS = 1000

# Which services each window is entitled to watch.
#
# This is a trust boundary, not a display preference. The Agent runs on the Payer's
# infrastructure; in production it would not be publishing to the Merchant's bus at
# all, and the Merchant would have no way to observe it. One bus serves both sides
# here so that one demo machine can tell the whole story — so the separation that
# deployment would enforce is enforced here instead, by never putting the other
# side's events on a window's connection.
#
# The Event Bus itself belongs to neither party's story. Each window's header
# already reports whether its connection is live, which is the only thing the bus's
# own activity would tell an operator.
WINDOWS = {
    "merchant": {"invoice-api", "ucp-server"},
    "agent": {"agent"},
}


def _after(events: deque, last_seen: str | None) -> list:
    """The tail of the history a window has not seen yet.

    An unrecognised id means the window was away longer than the history, so it gets
    everything still held rather than a silent gap.
    """
    if last_seen is None:
        return list(events)
    seen = [index for index, event in enumerate(events) if event.id == last_seen]
    return list(events)[seen[0] + 1 :] if seen else list(events)


def create_app(heartbeat_seconds: float = 15.0, history: int = 500) -> FastAPI:
    app = FastAPI(title="Event Bus")
    # Both windows are served from a different origin than the bus they read.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Each open connection, with the set of services it is entitled to see.
    subscribers: dict[asyncio.Queue, set[str] | None] = {}
    # The demo starts before anyone is watching: services announce themselves as they
    # come up, and the operator opens the windows afterwards. A window that arrives
    # late must still be able to tell the story from the beginning.
    recent: deque[Event] = deque(maxlen=history)
    # The bus is the one service that cannot announce itself over the network, so it
    # seeds its own arrival into the history the windows replay.
    recent.append(
        Event.of(
            Publication(
                type="service.started",
                service=SERVICE,
                payload={"service": SERVICE},
            )
        )
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "up", "windows_connected": len(subscribers)}

    @app.post("/events", status_code=202)
    async def publish(published: Publication) -> Event:
        event = Event.of(published)
        recent.append(event)
        for queue, watching in subscribers.items():
            if watching is None or event.service in watching:
                queue.put_nowait(event)
        return event

    @app.get("/events")
    async def subscribe(
        window: str | None = None,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        if window is not None and window not in WINDOWS:
            # Streaming nothing would look exactly like a quiet system, and the demo
            # would appear broken with no clue why.
            raise HTTPException(
                status_code=422,
                detail=f"no such window: {window}. Windows are {sorted(WINDOWS)}.",
            )
        # No window named means the whole thread across every service, which is what
        # an end-to-end test watches and what no single window is entitled to.
        watching = WINDOWS[window] if window else None

        # Subscribe before the response starts, so an event published the moment a
        # window connects cannot slip through the gap.
        queue: asyncio.Queue = asyncio.Queue()
        for missed in _after(recent, last_event_id):
            if watching is None or missed.service in watching:
                queue.put_nowait(missed)
        subscribers[queue] = watching

        async def frames():
            # Tells the window how soon to come back if this connection dies.
            yield f"retry: {RECONNECT_AFTER_MS}\n\n"
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(
                            queue.get(), timeout=heartbeat_seconds
                        )
                    except TimeoutError:
                        # A quiet system and a dead connection look identical to a
                        # window until the bus says something.
                        yield ": heartbeat\n\n"
                        continue
                    # The id is what a reconnecting window hands back as
                    # Last-Event-ID to say where it got to.
                    yield f"id: {event.id}\ndata: {event.model_dump_json()}\n\n"
            finally:
                subscribers.pop(queue, None)

        return StreamingResponse(frames(), media_type="text/event-stream")

    return app
