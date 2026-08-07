# Invoice Payment Demo

A local, user-controlled Agent that discovers Outstanding Invoices, evaluates them
against Policy the Payer wrote in plain English, and pays over UCP and AP2.

See `CONTEXT.md` for the domain glossary (binding on naming) and `docs/adr/` for the
decisions that look wrong without their context.

## Running the demo

```bash
docker compose up --build
```

Then open the two windows, each in its own browser window:

- Merchant — http://localhost:5173/merchant
- Agent — http://localhost:5173/agent

Each holds a live connection to the Event Bus and renders events as they arrive,
labelled with the service that emitted them. A window that is opened after the
system started still sees the startup events, and reconnects on its own if the
stream drops.

The two windows see different events, and that is a trust boundary rather than a
display preference: the merchant window is sent Invoice API and UCP Server activity,
the agent window is sent the Agent's, and neither connection ever carries the other
side's events. See ADR 0004.

## The system

| Service     | Stack                | Port | Role                                          |
| ----------- | -------------------- | ---- | --------------------------------------------- |
| Invoice API | Java, Spring Boot    | 8080 | The Merchant's system of record. UCP-unaware.  |
| UCP Server  | Python, FastAPI      | 8000 | Exposure layer over the Invoice API.           |
| Agent       | Python               | 8200 | The Payer's local Agent.                       |
| Event Bus   | Python, FastAPI      | 8100 | Fans every service's activity out over SSE.    |
| Web         | Vite, React          | 5173 | Both windows, as two routes.                   |

`docker compose up` orders startup by health, so no service is asked to publish to
an Event Bus that is not answering yet.

## The merchant window

The merchant window raises Invoices and lists them. The form takes a Payer email, an
amount, and a Due Date it offers thirty days out; everything else — the opaque Doc
Number, the currency, the Allowed Payment Methods — comes from the Invoice API, which
is the sole system of record.

The list is never updated by the form. It reloads when the Event Bus announces that an
Invoice changed, so an Invoice raised from another window, from `curl`, or eventually
by the Agent's payment arrives by exactly the same route as the operator's own:

```bash
curl -X POST localhost:8080/invoices \
  -H 'Content-Type: application/json' \
  -d '{"payerEmail":"vampserv@gmail.com","originalTotalMinorUnits":43000,"dueDate":"2019-03-28"}'
```

Every field but `payerEmail` and `originalTotalMinorUnits` may be left out: the Due
Date falls thirty days out, the currency is USD, and the Invoice takes bank or card.

## Driving a publish by hand

Each service exposes a ping that publishes one event, so a publish can be driven
from a chosen service:

```bash
curl -X POST localhost:8080/demo/ping   # invoice-api
curl -X POST localhost:8000/demo/ping   # ucp-server
curl -X POST localhost:8200/demo/ping   # agent
```

## Tests

```bash
cd services/event-bus && uv run pytest        # the Event Bus at its HTTP seam
cd services/invoice-api && ./mvn.sh test      # the Invoice API at its HTTP seam
cd web && npm run e2e                         # the merchant window, against the real stack
```

`mvn.sh` runs Maven in a container, so no local JDK is needed — the same assumption
the Dockerfiles make. `npm run e2e` brings the demo up with `docker compose` if it
isn't already running; note that it **reuses a stack that is already up**, so after
changing anything under `web/` or `services/`, rebuild before trusting a green run:

```bash
docker compose up --build --wait
```
