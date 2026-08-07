# Architecture, APIs, and what is not built

What the demo actually is as of this commit. `docs/overview.md` is the original brief —
the intent; this is the state. Where they disagree, this file is right and the gap is
listed at the bottom against the ticket that closes it.

## The shape

```
        Payer's side                 |            Merchant's side
                                     |
  +---------------------+            |     +---------------------+
  |  Agent  (:8200)     |            |     |  UCP Server (:8000) |
  |                     |  UCP/HTTP  |     |                     |
  |  Wakes              +------------------>  Discovery Profile  |
  |  Merchant client    |            |     |  Catalog Search     |
  |  Policy Engine (stub)            |     |  Invoice Extension  |
  +---------------------+            |     |  Checkout           |
                                     |     +----------+----------+
                                     |                | private REST
                                     |                v
                                     |     +---------------------+
                                     |     | Invoice API (:8080) |
                                     |     | Spring Boot + H2    |
                                     |     | SYSTEM OF RECORD    |
                                     |     +---------------------+

        Every service publishes to the Event Bus (:8100), which fans out over
        SSE to the two windows the Web app serves (:5173).
```

Five services under one `docker compose up --build`, ordered by health.

| Service | Stack | Port | Role |
| --- | --- | --- | --- |
| Invoice API | Java, Spring Boot, H2 | 8080 | Sole system of record. UCP-unaware. |
| UCP Server | Python, FastAPI | 8000 | Exposure layer. Stores no Invoice state. |
| Agent | Python, FastAPI | 8200 | The Payer's. Reaches the Merchant only over UCP. |
| Event Bus | Python, FastAPI | 8100 | SSE fan-out to the windows. |
| Web | Vite, React | 5173 | Both windows, as two routes. |

Three invariants hold the design together:

1. **The Invoice API is the only system of record.** Every Invoice fact the Agent holds
   came from it through UCP on that run. No caching anywhere, and the UCP Server writes
   no Invoice state.
2. **The Agent reaches the Merchant only over UCP** — discovery first, then the endpoint
   the profile published. It has no route to the Invoice API.
3. **The Event Bus scopes subscriptions by window**, and that is a trust boundary rather
   than a display choice (ADR 0004). `merchant` sees `invoice-api` and `ucp-server`;
   `agent` sees `agent`; neither sees the other's.

## APIs

**Invoice API (:8080)** — private REST, not UCP. No OpenAPI document.

| | |
| --- | --- |
| `POST /invoices` | Raise an Invoice. Only `payerEmail` and `originalTotalMinorUnits` required; Due Date defaults 30 days out, currency USD, bank + card. |
| `GET /invoices?payerEmail=` | Every Invoice, or one Payer's. |
| `POST /invoices/{id}/payments` | Apply a payment. `{"amountMinorUnits": n}`. 422 if settled or overpaying, 404 if unknown. |
| `GET /health`, `POST /demo/ping` | |

**UCP Server (:8000)** — OpenAPI at `/openapi.json`. Every route but discovery and the
schema takes `X-API-Key`, which names the Payer whose Invoices are in scope.

| | |
| --- | --- |
| `GET /.well-known/ucp` | Discovery Profile: version, capabilities, REST endpoint, mock payment handler. |
| `POST /catalog/search` | The Payer's Outstanding Invoices as Catalog products. Query and filters are read and ignored. |
| `POST /checkout` | Open a Checkout. Line item `item.id` is the Invoice id, quantity 1. |
| `GET /checkout/{id}` | |
| `POST /checkout/{id}/complete` | Settle. Body ignored — the handler is the mock one. 409 if already completed. |
| `GET /ucp/schemas/invoice.json` | The Invoice Extension's schema. |

Capabilities published: `dev.ucp.shopping.catalog.search`,
`dev.ucp.shopping.checkout`, and `com.lapins.demo.invoicing.invoice` (extends catalog
search).

**Agent (:8200)** — `POST /agent/wake` with `{"because": "..."}`, plus `/health` and
`/demo/ping`. One door in: every Wake enters here.

**Event Bus (:8100)** — `POST /events` to publish; `GET /events?window=merchant|agent`
to subscribe over SSE, with `Last-Event-ID` replay and a 500-event history. Unscoped
`GET /events` returns every service and exists for tests.

## What works

Raise an Invoice and it is paid with nothing pressed. The Agent wakes on
`invoice.created`, reads the Discovery Profile, negotiates capabilities, searches the
Catalog, reaches a Decision per Invoice, opens a Checkout, completes it — settlement
delegating to the Invoice API — and then re-reads the Catalog to confirm the Invoice is
no longer Outstanding rather than trusting the Checkout it just completed. Run Agent Now
raises the same Wake by hand.

Tests: 12 invoice-api, 22 ucp-server (+2 integration), 14 agent, 10 event-bus, 7 web
e2e.

## What is not built

Listed against the ticket that closes it. The first is the one that matters — everything
else is a capability; that one is the demo's headline claim.

| Not built | Ticket |
| --- | --- |
| **AP2 Mandates.** Nothing is cryptographically bound to the Merchant or the Checkout. The signing machinery is forked into the tree but unwired, so "the Merchant can tell a person authorized this from a model decided to" is currently asserted rather than shown. | `.8` |
| **The Policy Engine.** `agent/policy.py` allows every Invoice with the Reason Code `NO_POLICY_IN_FORCE`. No limits, no due-date logic, no DENY or REQUIRE_APPROVAL, no durable Decisions, no queues. Checkout completion is not gated on ALLOW. | `.5` |
| **Natural language to Policy.** No `claude -p`, no LLM anywhere in the Agent. | `.6`, `.10` |
| **The Approval loop.** No human approval, no Human-Present Mandates, no override of a Reason Code. | `.9` |
| **Partial payment.** UCP Checkout cannot express it, so the Agent always pays the full Balance Due. The Invoice API *does* accept a partial amount — the constraint lives in Checkout, where the limitation is. See `Notes.md`. | — |
| **Scheduler tick.** Two of the four Wakes are wired (Invoice created, Run Agent Now); the scheduler and the approval hook are not. | `.4`, `.9` |
| **Decline path.** The payment simulator only succeeds. | `.11` |
| **Multiple Merchants or Payers.** One seeded Merchant; one API key naming one Payer (`vampserv@gmail.com`). An Invoice raised against anyone else is invisible to the Agent. | — |
| **Identity linking / OAuth.** A static API key is the whole of authentication. | — |
| **The extension's `spec` link 404s.** The Discovery Profile advertises `com.lapins.demo.invoicing.invoice` with `spec: {endpoint}/ucp/extensions/invoice`, and only the `schema` URL beside it is served. Harmless to the run — the Agent never fetches it — but it is a dead link a curious reader will follow. | — |

Two known compromises, both deliberate and both written down where they live:

- **The Agent learns of Invoices by watching the Merchant's Event Bus**, which a Payer's
  Agent would have no place on. In production this is a webhook, an email, or a
  scheduled poll. Confined to `agent/wakes.py`; see the README.
- **The reference `checkout_service.py` is forked but not wired**, and a fresh Checkout
  written beside it, because the reference prices from its own SQLite products and
  inventory — which would make the exposure layer a second system of record. See
  `services/ucp-server/FORK.md`.
