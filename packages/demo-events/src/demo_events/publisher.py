"""Publishing to the Event Bus, from the point of view of a service that has work
to do and cannot afford to care whether the demo windows are watching."""

import logging

import httpx

logger = logging.getLogger(__name__)


class EventPublisher:
    """Announces one service's activity on the Event Bus."""

    def __init__(self, bus_url: str, service: str):
        self._service = service
        self._client = httpx.AsyncClient(base_url=bus_url, timeout=2.0)

    async def publish(
        self,
        type: str,
        correlation_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        try:
            await self._client.post(
                "/events",
                json={
                    "type": type,
                    "service": self._service,
                    "correlation_id": correlation_id,
                    "payload": payload or {},
                },
            )
        except httpx.HTTPError as unreachable:
            # The Event Bus is a window onto the demo, not a dependency of it. A
            # service whose work succeeded must not fail because nobody was watching.
            logger.warning("could not publish %s: %s", type, unreachable)

    async def aclose(self) -> None:
        await self._client.aclose()
