"""The shape of everything that crosses the Event Bus."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Publication(BaseModel):
    """What a service hands the Event Bus."""

    type: str
    service: str
    correlation_id: str | None = None
    payload: dict = Field(default_factory=dict)


class Event(BaseModel):
    """What the windows read: always attributed, always correlated."""

    id: str
    occurred_at: datetime
    type: str
    service: str
    correlation_id: str
    payload: dict

    @classmethod
    def of(cls, published: Publication) -> "Event":
        return cls(
            # Identity and time are settled once, here, so that two windows watching
            # the same event never disagree about which event it was or when it was.
            id=f"evt-{uuid.uuid4().hex[:12]}",
            occurred_at=datetime.now(UTC),
            type=published.type,
            service=published.service,
            # An event with no thread of its own starts one, so that nothing on the
            # stream is uncorrelated.
            correlation_id=published.correlation_id or f"corr-{uuid.uuid4().hex[:12]}",
            payload=published.payload,
        )
