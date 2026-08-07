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

## The cycle

Raise an Invoice in the merchant window and the Agent pays it, with nothing pressed.
The Agent reads the Merchant's Discovery Profile, negotiates capabilities,
searches the Catalog for the Payer's Outstanding Invoices, reaches a Decision on each,
pays those it may through a UCP Checkout, and then re-reads the Merchant's own records
to confirm the Invoice is settled rather than assuming it. The Invoice returns to the
merchant window as **Paid**, arriving by the event stream exactly as a payment made by
hand would.

**Run Agent Now** in the agent window raises the same Wake by hand, which is worth
having when the demo needs to be made to do something on cue. Both can be driven
without a browser:

```bash
# Raising an Invoice is enough; the Agent wakes on its own.
curl -X POST localhost:8080/invoices \
  -H 'Content-Type: application/json' \
  -d '{"payerEmail":"vampserv@gmail.com","originalTotalMinorUnits":43000}'

# Or wake it by hand.
curl -X POST localhost:8200/agent/wake \
  -H 'Content-Type: application/json' -d '{"because":"Run Agent Now"}'
```

**How the Agent knows an Invoice exists** is the demo's weakest joint, and worth being
straight about if anyone asks. It watches the Event Bus — which is the Merchant's, and
which a Payer's Agent would have no place on. In production the notification arrives as
a webhook the Payer registered, an email, or a scheduled poll of the Catalog. ADR 0004
already concedes the same compromise in the other direction, where the Agent publishes
to the Merchant's bus so that one screen can tell the whole story. It is confined to
`services/agent/src/agent/wakes.py`, and everything downstream of it is the ordinary
Wake path that Run Agent Now also uses.

The Agent holds one API key, and that key names one Payer — `vampserv@gmail.com`. An
Invoice raised against anybody else is invisible to it, which is the scoping working
rather than a bug.

**The Policy Engine is a stub**: it allows every Invoice, and says so with the Reason
Code `NO_POLICY_IN_FORCE`. `services/agent/src/agent/policy.py` is where real
evaluation goes. Nothing else in the demo is standing in for something — the discovery,
the Catalog, the Checkout, and the settlement are all real, and the Agent's language
model does not yet appear at all.

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
cd services/ucp-server && uv run pytest       # Catalog and Checkout, Invoice API stubbed
cd services/agent && uv run pytest            # a Wake through to a verified payment
cd web && npm run e2e                         # both windows, against the real stack
```

`services/ucp-server` also holds tests marked `integration` that run against the real
Java service; they are excluded by default and run with `uv run pytest -m integration`.

`mvn.sh` runs Maven in a container, so no local JDK is needed — the same assumption
the Dockerfiles make. `npm run e2e` brings the demo up with `docker compose` if it
isn't already running; note that it **reuses a stack that is already up**, so after
changing anything under `web/` or `services/`, rebuild before trusting a green run:

```bash
docker compose up --build --wait
```
