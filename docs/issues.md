# Issues

Generated from `.beads/issues.jsonl` by `scripts/render-issues.py`; edit issues with `bd`, not here. Regenerate with:

```bash
bd export -o .beads/issues.jsonl && python3 scripts/render-issues.py
```

**15 issues** — 11 open, 4 closed.

| | ID | Priority | Title |
| --- | --- | --- | --- |
| ○ | `intuit-ucp-8k9` | P3 | Discovery Profile advertises an extension spec URL that 404s |
| ○ | `intuit-ucp-90m` | P1 | Local agent pays invoices autonomously over UCP and AP2 |
| ✓ | `intuit-ucp-90m.1` | P1 | Walking skeleton: compose, event bus, live SSE in both windows |
| ✓ | `intuit-ucp-90m.2` | P1 | Invoice domain and merchant window create/list |
| ✓ | `intuit-ucp-90m.3` | P1 | UCP discovery profile and Invoice Extension over Catalog |
| ○ | `intuit-ucp-90m.4` | P1 | Agent skeleton, Wakes, and Discover Invoices |
| ○ | `intuit-ucp-90m.5` | P1 | Policy Engine, durable Decisions, and the two queues |
| ○ | `intuit-ucp-90m.6` | P1 | Natural language to Policy via claude -p |
| ○ | `intuit-ucp-90m.7` | P1 | Checkout, simulated payment, and Verify Payment |
| ○ | `intuit-ucp-90m.8` | P1 | AP2 Autonomous Mandates and verification |
| ○ | `intuit-ucp-90m.9` | P1 | Approval loop and Human-Present Mandates |
| ○ | `intuit-ucp-90m.10` | P1 | Language model orchestrates the full run |
| ○ | `intuit-ucp-90m.11` | P2 | Seed fixtures, decline path, and demo hardening |
| ✓ | `intuit-ucp-acl` | P1 | Demo spine: Invoice created, Agent discovers, Agent pays |
| ○ | `intuit-ucp-eg0` | P3 | Remove the walking-skeleton /demo/ping routes |

○ open · ◐ in progress · ✓ closed · ● blocked · ❄ deferred

---

## ○ Discovery Profile advertises an extension spec URL that 404s

`intuit-ucp-8k9` · open · P3 · bug

The Discovery Profile declares com.lapins.demo.invoicing.invoice with spec: {endpoint}/ucp/extensions/invoice, but only the schema URL beside it (/ucp/schemas/invoice.json) is served. Nothing in the demo fetches the spec link, so the run is unaffected — but it is a dead link in a published protocol document, and a reader following it during a demo gets a 404. Either serve human-readable extension documentation there or drop the key from the profile.

**Acceptance criteria**

Following every URL in the Discovery Profile returns 200

---

## ○ Local agent pays invoices autonomously over UCP and AP2

`intuit-ucp-90m` · open · P1 · feature · `ready-for-agent`

#### Problem Statement

Paying a supplier's invoices is a task a person performs by hand, repeatedly, against a
UI that already knows everything needed to make the decision. The Payer opens a link,
reads a list of Outstanding Invoices, checks each against rules they hold in their head
("nothing over $500", "only pay what's actually due", "always clear the full Balance
Due"), ticks boxes, and pays. The rules are stable; the labour is not.

Handing that labour to an agent has been blocked by a trust problem rather than a
capability one. An agent that can pay bills is an agent that can pay the wrong bill, for
the wrong amount, to the wrong Merchant. There has been no way for a Merchant to
distinguish "a person authorized this" from "a language model decided to", and no way
for a Payer to bound what their agent may do without simply not running it.

This demo shows the trust problem being solved: an autonomous, locally-run Agent that
discovers Outstanding Invoices, evaluates them against Policy the Payer wrote in plain
English, and completes payment — where every authorization is cryptographically bound to
the Merchant and the Checkout, and where the language model is structurally incapable of
authorizing anything on its own.

#### Solution

Three servers and two browser windows, run as one system under Docker Compose.

An **Invoice API Server** stands in for the invoicing product that exists today. It owns
Invoices, simulates payment, and knows nothing about UCP or agents.

A **UCP Server** sits in front of it as a pure exposure layer, publishing a UCP discovery
profile, a vendor Invoice Extension over the Catalog capability, Checkout, and AP2
Mandate verification. It is never the system of record.

A **local Agent** — the Payer's, not the Merchant's — turns natural-language instructions
into machine-readable Policy, discovers Invoices over UCP, evaluates each against Policy
using deterministic code, and pays those that pass. Its language model runs with no
filesystem, no shell, and exactly five callable Skills, so "the LLM cannot authorize
payment" is a property of the process rather than a promise in a prompt.

Two windows tell the story in real time, both fed by a single **Event Bus** over SSE. A
merchant window shows Invoice and UCP activity and can create new Invoices. An agent
window shows the Agent's reasoning and holds the queues of Invoices it declined or
referred — either of which a human may approve, which wakes the Agent to act.

#### User Stories

1. As a Payer, I want to describe my payment rules in plain English, so that I don't have
   to learn a policy syntax to delegate bill payment.
2. As a Payer, I want my instructions converted into a Policy I can read on screen, so
   that I can confirm the Agent understood me before it spends anything.
3. As a Payer, I want the Policy to be evaluated by deterministic code rather than by the
   language model, so that identical facts always produce an identical Decision.
4. As a Payer, I want the Agent to discover my Outstanding Invoices without my telling it
   where they are, so that delegation actually saves me the work.
5. As a Payer, I want the Agent to read Invoice facts from the Merchant's authoritative
   system, so that it never acts on a figure it inferred or remembered.
6. As a Payer, I want an Invoice that satisfies my Policy paid without my involvement, so
   that the routine case costs me nothing.
7. As a Payer, I want an Invoice above my per-Invoice limit refused, so that a large
   Invoice can never be paid by autonomy alone.
8. As a Payer, I want an Invoice that isn't due yet left unpaid, so that the Agent doesn't
   drain my account early.
9. As a Payer, I want a not-yet-due Invoice reconsidered automatically as its Due Date
   approaches, so that a deferral doesn't become a permanent refusal.
10. As a Payer, I want Invoices needing my judgement surfaced in a queue, so that the
    exceptional case reaches me rather than being silently dropped.
11. As a Payer, I want to see the Reason Code behind every refusal, so that I understand
    why the Agent stopped rather than having to guess.
12. As a Payer, I want to approve an Invoice the Agent referred to me, so that I can
    release a payment the Policy wouldn't release on its own.
13. As a Payer, I want to approve an Invoice the Agent flatly refused, so that my
    authority outranks the constraints I set for the Agent.
14. As a Payer, I want my approval recorded against the Reason Code it overrode, so that
    the override is auditable rather than invisible.
15. As a Payer, I want an approval to be acted on promptly without my pressing anything
    else, so that approving is one click rather than a workflow.
16. As a Payer, I want the Agent to keep my declined and referred Invoices across
    restarts, so that a queue isn't lost when a process dies.
17. As a Payer, I want the Agent to explain each action in readable language, so that I
    can follow what it did without reading logs.
18. As a Payer, I want the Agent's language model to hold no capability beyond its five
    Skills, so that no prompt can talk it into an action I didn't sanction.
19. As a Payer, I want authorization cryptographically bound to a specific Merchant and
    Checkout, so that an authorization cannot be replayed against a different payment.
20. As a Payer, I want the Agent to confirm the Invoice is settled by re-reading the
    Merchant's state after paying, so that success is verified rather than assumed.
21. As a Payer, I want the Agent to pay the complete Balance Due when my Policy requires
    it, so that a part-payment never leaves an Invoice quietly Outstanding.
22. As a Payer, I want to run the Agent on demand, so that I can act without waiting for
    the schedule.
23. As a Merchant operator, I want to create an Invoice with a client, amount, and Due
    Date, so that I can produce any scenario on demand.
24. As a Merchant operator, I want a newly created Invoice to wake the Agent immediately,
    so that the system demonstrably reacts to events rather than only to polling.
25. As a Merchant operator, I want the Agent woken for every new Invoice regardless of Due
    Date, so that Policy rather than the trigger decides what happens.
26. As a Merchant operator, I want to see my Invoices and their current state, so that I
    can confirm what the Agent actually changed.
27. As a Merchant operator, I want Invoice and UCP activity labelled by which server
    emitted it, so that I can tell the exposure layer's behaviour from the system of
    record's.
28. As a Merchant, I want to remain the sole system of record for Invoice state, so that
    the UCP layer can be changed or removed without risking my data.
29. As a Merchant, I want to verify that an Agent's Mandate is bound to me before
    settling, so that I don't honour an authorization intended for someone else.
30. As a Merchant, I want to distinguish an Autonomous Mandate from a Human-Present
    Mandate, so that I know whether a person was actually present.
31. As a Merchant, I want to expose Invoices through the published Catalog capability
    rather than a bespoke endpoint, so that any conforming agent can find them.
32. As a Merchant, I want Invoice-specific meaning carried by a namespaced vendor
    extension, so that I add domain semantics without forking the protocol.
33. As a Merchant, I want to publish a discovery profile at a well-known location, so that
    an Agent can negotiate capabilities without prior arrangement.
34. As a Merchant, I want each Invoice to declare its Allowed Payment Methods, so that the
    exposed data mirrors the real product.
35. As an Agent, I want to negotiate capabilities before acting, so that I only attempt
    operations the Merchant actually supports.
36. As an Agent, I want a single mechanism to begin work — a Wake — so that scheduled,
    event-driven, approval-driven, and manual starts all follow one path.
37. As an Agent, I want to end my run rather than block when a human's Decision is needed,
    so that no model turn is ever held open on a person's attention.
38. As an Agent, I want to resume from persisted Decisions on each Wake, so that I don't
    depend on a conversation surviving between runs.
39. As an Agent, I want to assemble multiple Invoices into a single Checkout, so that
    paying several at once matches how the reference product behaves.
40. As an Agent, I want to evaluate each Invoice separately before assembling a Checkout,
    so that one refused Invoice doesn't block the others.
41. As a demo viewer, I want events to stream live into both windows, so that I can watch
    the system react rather than read a summary afterwards.
42. As a demo viewer, I want a single event to be traceable from Invoice through Decision,
    Checkout, Mandate, and payment, so that I can follow one story across three servers.
43. As a demo viewer, I want a refusal followed by a human approval and a successful
    payment, so that I see both the constraint and the escape hatch.
44. As a demo operator, I want the whole system to start with one command, so that setup
    isn't part of the presentation.
45. As a demo operator, I want seeded Invoices that produce an approval, a refusal, and a
    referral without my creating anything, so that the demo works before I touch it.

#### Implementation Decisions

**Service topology.** Four backend services plus one frontend, orchestrated by Docker
Compose: Invoice API Server (Java, Spring Boot, Spring Web, Spring Data JPA, H2), UCP
Server (Python, FastAPI), Agent (Python), Event Bus (small SSE service), and a Vite
single-page app served as two routes opened in two browser windows.

**UCP Server provenance.** Forked from the Python reference merchant server in
`Universal-Commerce-Protocol/samples`, retaining its protocol, checkout, validation,
signing, and authorization infrastructure, and depending on the official `ucp-sdk`.
Recorded as ADR 0001; the Node sample was rejected because it carries no AP2 support.

**Agent language.** Python, chosen so the Agent shares `ucp-sdk` types with the UCP
Server rather than maintaining a second set of protocol models.

**Invoice Extension.** A vendor extension `com.lapins.demo.invoicing.invoice` declaring
`extends: ["dev.ucp.shopping.catalog"]`, composed into the server's models the way the
reference sample composes its existing extension mixins. It exposes Invoice fields only —
Doc Number, Due Date, Balance Due, original total, Outstanding and Overdue state,
currency, Allowed Payment Methods, Merchant, Payer — and delegates all search to the
Invoice API Server. It stores nothing.

**Invoice data model.** Derived from the reference payment UI. An Invoice carries a Doc
Number that is opaque and not sequential, a Due Date, a Balance Due that may be less than
the original total, a currency, Allowed Payment Methods, and a Payer identified by email.
A Merchant carries a name, contact email, and free-text payment instructions.

**Discovery and negotiation.** The UCP Server publishes a profile at `/.well-known/ucp`
declaring its capabilities, versions, and REST endpoint. The Agent reads it and negotiates
the capability intersection before acting.

**Payer scoping.** The Agent authenticates with a static API key that resolves to a
Payer; Catalog search is scoped to that Payer's Invoices. `dev.ucp.common.identity_linking`
is deliberately not implemented.

**Checkout.** Uses the published Checkout capability. An Invoice becomes a line item with
a quantity of one, and a Checkout may carry several. Settlement delegates to the Invoice
API Server, which records payments per Invoice.

**AP2 authorization.** Mandates are genuine ES256 JWS, signed by the Agent and verified by
the UCP Server, with claims binding the Mandate to the Merchant, the Checkout, and the
amount. SD-JWT selective disclosure is deliberately not implemented. Two Mandate kinds
exist and are not interchangeable: an Autonomous Mandate carries only Policy authority; a
Human-Present Mandate carries an Approval and records the Reason Code it overrode.
Recorded as ADR 0003.

**Policy schema.** Generated by the language model under a JSON Schema constraint, shaped
as `{merchant, pay_when_due_within_days, maximum_payment_per_invoice, currency,
full_balance_only}`. Amounts are integer minor units. The per-Invoice cap is named for
what it is — it bounds each Invoice, not a Checkout total, which mirrors how corporate
spending limits actually work.

**Policy Engine.** A pure function over `(Policy, Invoice, now)` returning a Decision of
ALLOW, DENY, or REQUIRE_APPROVAL with Reason Codes. An Overdue Invoice counts as due, so
the due-window test is `dueDate - now <= pay_when_due_within_days` with no lower bound. A
not-yet-due Invoice is `DENY / NOT_YET_DUE`, re-evaluated on each Wake, which needs no
fourth verdict and self-corrects as the Due Date nears. Checkout completion is impossible
unless the current Decision is ALLOW or an Approval exists.

**Skills.** Five Skills — Configure Payment Policy, Discover Invoices, Evaluate Invoice,
Pay Invoice, Verify Payment — served to the model over MCP by the Agent process.

**Language model confinement.** The Agent invokes `claude -p` as a subprocess with
`--tools ""`, `--strict-mcp-config`, `--setting-sources ""`, `--disable-slash-commands`,
and a replaced system prompt, so the model's entire action space is the five Skills.
`--bare` is not used because it cannot read subscription credentials; authentication is by
`CLAUDE_CODE_OAUTH_TOKEN` supplied through the environment. Structured Policy output uses
`--json-schema`; the run streams as `stream-json` into the Event Bus. The subprocess sits
behind an interface so it can be substituted.

**Wakes.** The Agent has exactly four Wake sources — an Invoice created, an Approval
granted, a scheduler tick, and Run Agent Now — and no other way to begin. A Wake never
blocks: when a Decision needs a human, the Agent persists it, ends the run, and a later
Approval arrives as a fresh Wake. Recorded as ADR 0002.

**Decision store.** The Agent persists Decisions in its own store so referral and refusal
queues survive restarts and so each run resumes from state rather than from conversation
history.

**Approval.** Both the refused and the referred queues are approvable, and any DENY may be
approved including a limit breach. Approval is a human act, never performed by the model,
and produces a Human-Present Mandate.

**Event Bus.** A separate service, deliberately not folded into the Invoice API Server,
which must stay UCP-unaware — the UCP Server publishes Mandate verification events that an
Invoice-API-hosted bus would have to understand. All services publish to it; it exposes
SSE to both windows. Every event carries a correlation identifier threading Invoice →
Decision → Checkout → Mandate → payment, and identifies its emitting service.

**Payment simulation.** Deterministic, supporting success and decline outcomes, with no
credentials and no money movement.

**Merchant window.** Streams Invoice API and UCP Server events with the emitter labelled,
lists Invoices, and creates an Invoice from client, amount, and Due Date.

**Agent window.** Streams the Agent's output and Decisions, and presents the refused and
referred queues as separate lists, each item approvable.

#### Testing Decisions

**What makes a good test here.** Tests assert externally observable behaviour — the events
the system emits and the state the Invoice API reports — never internal call sequences,
private methods, or the wording of model output. A test that would fail if the Agent were
rewritten while preserving its behaviour is testing the wrong thing.

**The primary seam is the Event Bus stream, driven by a Wake.** Because every service
already publishes there for the windows' benefit, tests need no bespoke observation
points. A test injects a Wake — usually by creating an Invoice — and asserts the ordered
sequence of events with their correlation identifier, exercising the real Invoice API,
real UCP Server, real Policy Engine, and real Mandate verification together. This is the
highest seam available and the great majority of coverage should sit here.

**The Policy Engine is additionally tested directly**, as a pure function over
`(Policy, Invoice, now)`. This is strictly redundant with the seam above, and justified
only because it is the component the whole authorization story rests on and because
exhaustive table-driven cases across due-window boundaries, the per-Invoice cap, the
full-Balance-Due rule, and currency mismatch are cheap there and slow through the bus.

**The language model is substituted, not exercised.** Tests inject a scripted runner
through the subprocess interface, so runs are deterministic, free, and fast. One
manually-run smoke test exercises the live model to confirm the Skills are callable and
the Policy schema holds; it is not part of the automated suite.

**Coverage to reach through the primary seam:** an Invoice satisfying Policy paid
end-to-end and verified against Invoice API state; an Invoice refused on the per-Invoice
cap; an Invoice deferred as `NOT_YET_DUE` and then allowed once inside the due window; a
referred Invoice approved by a human, producing a Human-Present Mandate; a refused Invoice
approved by a human, with the overridden Reason Code recorded; a Mandate bound to the
wrong Merchant or Checkout rejected by verification; a Checkout carrying several Invoices;
a declined payment leaving the Invoice Outstanding; Decisions surviving an Agent restart.

**Prior art.** The forked Python reference server ships integration tests, signature
integration tests, and signing tests — its integration-test style is the model for the
UCP Server's own tests, and its signing tests are the pattern for Mandate verification.
No other prior art exists; this is a greenfield repository.

#### Out of Scope

A complete implementation of the invoicing service — only what the demo flow requires,
per the reference UI. Real payment credentials, real money movement, and any real payment
processor. SD-JWT selective disclosure. `dev.ucp.common.identity_linking` and any OAuth
flow. Partial-payment *flows*: Balance Due and original total diverge in the data and one
seeded Invoice is already part-paid, but nothing in the system proposes paying less than
the Balance Due. Any Policy rule reading Allowed Payment Methods — the field exists to
mirror the real product, and gates nothing. Multi-Merchant support. Production concerns:
authentication beyond a static API key, key rotation, rate limiting, horizontal scaling,
and persistence beyond H2 and the Agent's local store. Cart and Order capabilities beyond
what Checkout requires.

#### Further Notes

The reference UI at the Intuit link in `docs/overview.md` is no longer reachable — it
returns a service-unavailable page. The Invoice data model in this spec is derived from a
screenshot captured on 2026-08-07, which remains the only evidence of the reference
product's shape. Three details from it are load-bearing and absent from the original
overview: partial payment is a real capability in the product, payment-method eligibility
varies per Invoice, and the product settles a multi-Invoice selection as separate
transactions.

`CONTEXT.md` holds the domain glossary and should be treated as binding on naming. Two
terms carry deliberate weight: **Payer** rather than "customer", because the person paying
in the reference UI arrived on an unauthenticated link and holds no account; and
**Approval** as a thing distinct from Policy authority, because the difference between
them is exactly what AP2 exists to express.

The `docs/overview.md` architecture diagram places the Event Service inside the Invoice
API Server. This spec deliberately departs from that, for the reason given under Event
Bus.

### ✓ Walking skeleton: compose, event bus, live SSE in both windows

`intuit-ucp-90m.1` · closed · P1 · task · `ready-for-agent`

##### What to build

A demo operator runs one command and the whole system comes up: Invoice API Server, UCP
Server, Agent, Event Bus, and the single-page app serving both windows. Any service can
publish an event to the Event Bus and both windows render it live as it arrives, each
event identifying which service emitted it. No domain behaviour yet — this is the thread
through every layer that later tickets widen.

##### Acceptance criteria

- [ ] One command brings up all four services and the UI, with startup ordering handled
- [ ] Event Bus accepts publishes from any service and fans out over SSE
- [ ] Merchant window and agent window each open as their own route and hold a live connection
- [ ] Every event carries an emitting-service identifier and a correlation identifier
- [ ] A window reconnects on its own when the stream drops
- [ ] A test drives a publish and asserts it arrives on the stream

**Notes**

--- UPDATE: window scoping ---
Alex caught that both windows showed every event. The parent spec already said
otherwise (merchant window = Invoice API + UCP Server; agent window = the Agent), and
his reason goes further: the Agent runs on the Payer's infrastructure, so the Merchant
should never RECEIVE its events, not merely hide them.

Filtering is therefore in the Event Bus, not the client. A window names itself
(GET /events?window=merchant|agent) and gets only what it is entitled to see.
Unscoped GET /events still returns everything — that is what the end-to-end tests in
later tickets need for the full Invoice -> Decision -> Checkout -> Mandate thread.

3 more tests at the same seam (10 total, all green):
- the merchant window is never sent the Agent's events (replayed and live)
- the agent window is never sent the Merchant's events (replayed and live)
- a stream asked for by a name that is not a window is refused 422

The Event Bus's own service.started now appears in no window; each window header
already reports whether its connection is live.

Recorded as ADR 0004 — a future reader will see the Agent publishing to the Merchant's
bus and try to 'fix' it.

**Closed** — Walking skeleton complete. One command brings up all four services and the UI ordered by health; every service publishes to the Event Bus and both windows render live, audience-scoped streams with emitter and correlation identifiers; windows reconnect on their own. 10 tests at the Event Bus HTTP seam. Windows confirmed rendering correctly by Alex.

### ✓ Invoice domain and merchant window create/list

`intuit-ucp-90m.2` · closed · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.1`

##### What to build

A Merchant operator creates an Invoice from a client, an amount, and a Due Date, sees it
appear in the Invoice list, and watches the creation event stream into the merchant
window. The Invoice API Server owns this state authoritatively and knows nothing about
UCP or agents.

The data model is derived from the reference payment UI screenshot: an Invoice carries an
opaque non-sequential Doc Number, a Due Date, a Balance Due that may be less than the
original total, a currency, and Allowed Payment Methods; a Payer is identified by email;
a Merchant carries a name, contact email, and free-text payment instructions.

##### Acceptance criteria

- [ ] Invoice, Merchant, and Payer persist in the Invoice API Server
- [ ] Create-invoice form takes client, amount, and Due Date, defaulting the Due Date 30 days out
- [ ] Invoice list shows Doc Number, Due Date, Balance Due, and whether Outstanding or Overdue
- [ ] Creating an Invoice emits an event that reaches the merchant window
- [ ] Balance Due and original total are separate fields that can legitimately differ
- [ ] Allowed Payment Methods is present per Invoice
- [ ] Doc Numbers are opaque, not sequential integers

**Notes**

--- Seams, confirmed with Alex before any test was written ---
Two: the Invoice API's HTTP boundary (Java, with a stub Event Bus recording what the
server publishes), and Playwright driving the merchant window against the real
docker compose stack. Alex chose Playwright over component tests with mocked I/O,
so the UI criteria are covered against the real Invoice API and real Event Bus.

--- Deliberately deferred ---
'Balance Due and original total are separate fields that can legitimately differ' is
met structurally, not demonstrably: two columns, two fields in the representation,
always equal until something pays. Alex chose this over adding a partial-payment
mechanism that belongs to .7. Recorded on .11, which needs a part-paid seed.

--- Naming ---
The ticket says the form takes a 'client'. CONTEXT.md lists Client under _Avoid_ for
Payer, and CONTEXT.md is binding, so the field is 'Payer email' throughout.

--- Notes for the next ticket ---
GET /invoices?payerEmail= exists already; .3 needs it for Payer-scoped Catalog
search. invoice.created carries the Invoice's own id as the correlation identifier,
so the Decision, Checkout, Mandate and payment thread onto the Invoice itself.
Maven runs in a container via services/invoice-api/mvn.sh — there is no local JDK.
web/ has no bind mount, so 'npm run e2e' reuses a running stack: rebuild after
changing web sources or the run is green against stale code.

**Closed** — Invoice, Merchant and Payer persist in the Invoice API Server (JPA/H2); the merchant window raises Invoices and lists them by Doc Number, Due Date, Balance Due and Outstanding/Overdue. Doc Numbers are opaque 8-character tokens, never a counter. Creating an Invoice publishes invoice.created correlated on the Invoice's own id, and the list reloads only from that event — proven by a test that raises an Invoice outside the browser entirely. 12 tests at the Invoice API HTTP seam, 4 Playwright tests against the real stack; the Event Bus's 10 still pass. One criterion met structurally rather than demonstrably: Balance Due and original total are separate fields but nothing can yet make them differ, per Alex's call, noted on .11.

### ✓ UCP discovery profile and Invoice Extension over Catalog

`intuit-ucp-90m.3` · closed · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.2`

##### What to build

An agent that has never seen this Merchant before reads the discovery profile, negotiates
capabilities, and searches the Catalog to retrieve that Payer's Outstanding Invoices —
with every Invoice fact coming from the Invoice API Server, which remains the sole system
of record.

Fork the Python reference merchant server per ADR 0001, retaining its protocol, checkout,
validation, signing, and authorization infrastructure.

##### Acceptance criteria

- [ ] Discovery profile published at the well-known location, declaring capabilities, versions, and REST endpoint
- [ ] Vendor extension com.lapins.demo.invoicing.invoice declares the Catalog capability as its parent
- [ ] The extension exposes only Invoice fields and stores nothing
- [ ] Catalog search delegates entirely to the Invoice API Server
- [ ] A static API key resolves to a Payer and scopes search to that Payer's Invoices
- [ ] UCP Server activity streams to the merchant window labelled as its own
- [ ] A test asserts a Catalog search returns Invoices created through the Invoice API

**Closed** — Discovery profile at /.well-known/ucp declares protocol version, Catalog Search + Checkout capabilities, and a REST endpoint taken from the request rather than configured. Vendor extension com.lapins.demo.invoicing.invoice extends dev.ucp.shopping.catalog.search and publishes its own fetchable, self-describing schema (ADR 0005 records why it is served from the Merchant rather than lapins.com). The extension exposes exactly nine Invoice fields, enforced by extra=forbid, and stores nothing: every Catalog search re-reads the Invoice API. A static API key resolves to a Payer and scopes the search at the Invoice API request, so another Payer's Invoices never cross the wire; no key and an unknown key are both 401 in the UCP envelope. The UCP Server publishes ucp.catalog_searched, labelled as its own, and an integration test watches it arrive on a real window=merchant subscription. Python reference merchant server forked whole per ADR 0001, provenance and every departure recorded in services/ucp-server/FORK.md. 13 tests at the UCP HTTP seam over a stubbed Invoice API, plus 2 integration tests against the whole demo under Compose that raise a real Invoice on the Java service and find it through the real Catalog. Follow-up intuit-ucp-eg0 filed for the walking-skeleton /demo/ping routes.

### ○ Agent skeleton, Wakes, and Discover Invoices

`intuit-ucp-90m.4` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.3`

##### What to build

The Agent begins work only when woken, and has exactly four ways to be woken: an Invoice
created, a scheduler tick, Run Agent Now, and an Approval granted (wired but unexercised
until the approval ticket). On each Wake it negotiates capabilities with the Merchant and
runs Discover Invoices, streaming its activity into the agent window.

Per ADR 0002, a Wake never blocks: a run reads persisted state, does its work, and ends.

##### Acceptance criteria

- [ ] Creating an Invoice in the merchant window wakes the Agent immediately, whatever its Due Date
- [ ] Scheduler tick, Run Agent Now, and the approval hook all enter the same single Wake path
- [ ] The Agent negotiates the capability intersection before acting
- [ ] Discovered Invoices appear in the agent window
- [ ] A run reads persisted state rather than carrying conversation between runs
- [ ] A test injects a Wake and asserts discovery events on the stream with a shared correlation identifier

### ○ Policy Engine, durable Decisions, and the two queues

`intuit-ucp-90m.5` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.4`

##### What to build

Every discovered Invoice gets a Decision from deterministic code — ALLOW, DENY, or
REQUIRE_APPROVAL with machine-readable Reason Codes — and the Payer sees refused and
referred Invoices as two separate lists in the agent window, each showing why. Policy is
hardcoded for now; the next ticket generates it.

Decisions are durable and outlive the run that produced them.

##### Acceptance criteria

- [ ] Policy Engine is a pure function over Policy, Invoice, and current time
- [ ] An Overdue Invoice counts as due — the due-window test has no lower bound
- [ ] A not-yet-due Invoice is DENY with reason NOT_YET_DUE and is re-evaluated on each Wake
- [ ] maximum_payment_per_invoice bounds each Invoice, never a Checkout total
- [ ] Refused and referred Invoices render as separate lists showing their Reason Codes
- [ ] Decisions survive an Agent restart
- [ ] Table-driven tests cover due-window boundaries, the per-Invoice cap, full-Balance-Due, and currency mismatch

**Notes**

The Policy Engine's seam now exists and is stubbed: services/agent/src/agent/policy.py returns ALLOW for every Invoice with the Reason Code NO_POLICY_IN_FORCE, and agent/run.py already publishes agent.decided per Invoice with verdict and reason codes. Real evaluation, durable Decisions and the two queues replace the stub; the shape (code reads Invoice facts, returns a verdict plus machine-readable Reason Codes, LLM absent) is already in place.

### ○ Natural language to Policy via claude -p

`intuit-ucp-90m.6` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.5`

##### What to build

The Payer types payment rules in plain English and sees the resulting machine-readable
Policy on screen before anything is spent. Deliberately the narrowest possible first
integration of the language model — one Skill, no payment path — so the local-model route
is de-risked while it is still cheap to change course.

Per ADR 0003 the model's action space is the Skills served to it and nothing else.

##### Acceptance criteria

- [ ] The claude -p subprocess sits behind an interface that tests can substitute
- [ ] Configure Payment Policy is served over MCP and is the only tool available in this run
- [ ] Output is constrained by JSON Schema to the Policy shape
- [ ] The model runs with no filesystem, no shell, and no discovered hooks, skills, or settings
- [ ] Authentication is by subscription token supplied through the environment
- [ ] The generated Policy is displayed in the agent window and activates the Policy Engine
- [ ] Tests run against a scripted runner, never a live model

### ○ Checkout, simulated payment, and Verify Payment

`intuit-ucp-90m.7` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.5`

##### What to build

An Invoice the Policy Engine allowed is paid end to end: the Agent creates a UCP Checkout
carrying it as a quantity-one line item, settlement delegates to the Invoice API Server's
deterministic simulator, and the Agent re-reads authoritative state to confirm the Invoice
is settled rather than assuming it.

A Checkout may carry several Invoices, which the reference product settles as separate
transactions.

##### Acceptance criteria

- [ ] Checkout uses the published Checkout capability, each Invoice a line item of quantity one
- [ ] A Checkout may carry several Invoices, settled per Invoice
- [ ] Settlement delegates to the Invoice API Server, which alone changes Invoice state
- [ ] Verify Payment re-reads authoritative state and confirms the Invoice is no longer Outstanding
- [ ] When Policy requires the full Balance Due, no partial amount is ever proposed
- [ ] Checkout completion is impossible unless the current Decision is ALLOW
- [ ] A test drives a Wake and asserts the full event sequence through to the Invoice being Paid

### ○ AP2 Autonomous Mandates and verification

`intuit-ucp-90m.8` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.7`

##### What to build

Before settling, the Merchant verifies that the Agent's authorization is cryptographically
bound to this Merchant and this Checkout — so an authorization cannot be replayed against
a different payment, and a Mandate bound elsewhere is refused.

Per ADR 0003, Mandates are genuine ES256 JWS with claims binding Merchant, Checkout, and
amount. SD-JWT selective disclosure is deliberately out of scope.

##### Acceptance criteria

- [ ] The Agent signs an Autonomous Mandate carrying only Policy authority
- [ ] Claims bind the Mandate to the Merchant, the Checkout, and the amount
- [ ] The UCP Server verifies before settling and refuses on a failed binding
- [ ] A Mandate bound to the wrong Merchant is rejected
- [ ] A Mandate bound to a different Checkout is rejected
- [ ] Verification outcomes stream to both windows
- [ ] Tests cover both a valid Mandate and each rebinding failure

### ○ Approval loop and Human-Present Mandates

`intuit-ucp-90m.9` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.8`

##### What to build

The Payer approves an Invoice from either queue — including one the Policy Engine flatly
refused, such as a breach of the per-Invoice cap — and the payment proceeds promptly
without them pressing anything else. The resulting authorization is visibly a different
kind from an autonomous one, and records what it overrode.

Per ADR 0003, Policy constrains the Agent, not the Payer. Per ADR 0002, approval is a
Wake rather than a blocking call.

##### Acceptance criteria

- [ ] Both the refused and the referred lists are approvable
- [ ] Any DENY may be approved, including a per-Invoice limit breach
- [ ] Approving emits a Wake carrying the approval; nothing blocks waiting for a human
- [ ] The result is a Human-Present Mandate, not interchangeable with an Autonomous one
- [ ] The Mandate records the Reason Code it overrode, so the override is auditable
- [ ] Approval is never performed by the language model
- [ ] Tests cover approving a referral and approving a hard refusal

### ○ Language model orchestrates the full run

`intuit-ucp-90m.10` · open · P1 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.9`, `intuit-ucp-90m.6`

##### What to build

The Agent stops being driven by hardcoded sequencing: the language model reads the Payer's
instructions, discovers Invoices, passes authoritative facts to the Policy Engine,
orchestrates Checkout and payment, verifies the result, and explains each action in
readable language — while remaining structurally incapable of authorizing a payment
itself.

##### Acceptance criteria

- [ ] All five Skills are served over MCP and are the model's entire action space
- [ ] The model cannot override a Decision from the Policy Engine
- [ ] The run streams token by token into the agent window through the Event Bus
- [ ] The model produces readable explanations of what it did and why
- [ ] Authoritative Invoice facts always come from the Merchant, never from model recall
- [ ] Tests use a scripted runner; a separate manual smoke test exercises the live model

### ○ Seed fixtures, decline path, and demo hardening

`intuit-ucp-90m.11` · open · P2 · task · `ready-for-agent`

**Blocked by** `intuit-ucp-90m.10`

##### What to build

A demo operator starts the system and already has a story to tell without creating
anything: seeded Invoices that produce an approval, a refusal, and a referral, plus the
fixtures that make the data mirror the real product.

##### Acceptance criteria

- [ ] Seeded Invoices yield one ALLOW, one DENY on the per-Invoice cap, and one REQUIRE_APPROVAL
- [ ] One seeded Invoice is already part-paid, so Balance Due and original total visibly differ
- [ ] One seeded Invoice is card-only, mirroring the reference product
- [ ] The payment simulator's decline outcome leaves the Invoice Outstanding
- [ ] A refusal followed by human approval and successful payment runs cleanly end to end
- [ ] Restarting the system leaves queues and Decisions intact

**Notes**

--- FROM .2: no way yet to raise a part-paid Invoice ---
Alex chose in .2 to leave Balance Due and original total as separate columns that
are always equal at creation: POST /invoices takes originalTotalMinorUnits only and
Balance Due starts equal to it. Nothing in the system can make them differ until
payment lands in .7.

So the criterion 'one seeded Invoice is already part-paid' has no mechanism behind
it yet. Seeding it needs either a partial settlement through .7's simulator, or a
way for the Invoice API to accept an opening Balance Due below the total. That is a
decision for whoever picks this up, not an oversight.

---

## ✓ Demo spine: Invoice created, Agent discovers, Agent pays

`intuit-ucp-acl` · closed · P1 · feature

Time-boxed reduction of .4/.5/.7 to the shortest path that shows a complete cycle on screen: an Invoice is raised in the merchant window, the Agent is woken by Run Agent Now, discovers it over UCP Catalog, pays it through a UCP Checkout, and the merchant window shows it settled.

Deliberately dropped for time: the Policy Engine (the Agent is hardwired to ALLOW everything), NL-to-Policy via claude -p (.6), AP2 Mandates (.8), the Approval loop (.9), LLM orchestration (.10). Auto-wake on invoice-created is also dropped; the wake is a human pressing Run Agent Now.

The forked upstream CheckoutService is deliberately NOT wired: its complete_checkout, _validate_inventory and _recalculate_totals read products, inventory and stock out of SQLite tables this demo never writes to, and populating them would make something other than the Invoice API a system of record. A thin Checkout is written instead, delegating settlement to the Invoice API.

**Acceptance criteria**

An Invoice raised in the merchant window is discovered, paid and shown settled, driven only by pressing Run Agent Now

**Closed** — Full cycle works end to end and is covered at every seam: invoice raised, discovered over UCP Catalog, decided on, paid through Checkout, verified by re-reading the Merchant. 6 web e2e, 8 agent, 22 ucp-server, 10 event-bus, 12 invoice-api tests green.

---

## ○ Remove the walking-skeleton /demo/ping routes

`intuit-ucp-eg0` · open · P3 · task

**Blocked by** `intuit-ucp-90m.4`

All three services (invoice-api, ucp-server, agent) carry a POST /demo/ping route from intuit-ucp-90m.1, which existed to prove a service could publish to the Event Bus before any of them had real activity to publish. The UCP Server now publishes ucp.catalog_searched, and the Invoice API publishes invoice.created; once the Agent publishes its own activity in intuit-ucp-90m.4, all three scaffolds are dead and should go together. Removing them piecemeal leaves the demo inconsistent, which is why it was not done in .3.
