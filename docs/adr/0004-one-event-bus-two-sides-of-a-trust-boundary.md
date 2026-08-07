# One Event Bus spans a boundary that production would split in two

The Agent publishes to the same Event Bus as the Invoice API and the UCP Server, and
that is wrong in every way except the one that matters for a demo. The Agent is the
Payer's, running on the Payer's infrastructure; the bus is the Merchant's side of the
world. In production there is no such bus, the Merchant cannot observe the Agent at
all, and the Agent's reasoning never leaves the Payer's machine. Two buses would model
that honestly, and would also mean two streams, two connections, and a demo that no
longer fits on one screen.

So there is one bus, and the separation that deployment would enforce is enforced at
subscription instead. A window names itself — `GET /events?window=merchant` or
`?window=agent` — and receives only the services that window is entitled to watch.
The Merchant's browser never receives an Agent event, rather than receiving it and
declining to draw it. The unscoped `GET /events` returns every service's events and
exists for end-to-end tests, which need the whole thread across all three servers;
no window is entitled to it.

## Consequences

`WINDOWS` in the Event Bus is a trust boundary and should be read as one. Adding a
service means deciding which side of the boundary it sits on, and a service on
neither side appears in no window — which is the case for the Event Bus itself, whose
liveness each window already reports from its own connection.

A window asking for a name that is not a window is refused rather than served an
empty stream, because during a demo an empty stream and a quiet system look identical.

If this demo ever grows a real deployment story, the seam to cut along is already
drawn: the Agent's publishes and the agent window become a second bus on the Payer's
side, and nothing about the Merchant's services changes.
