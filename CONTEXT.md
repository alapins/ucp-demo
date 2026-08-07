# Invoice Payment Demo

A demonstration of a local, user-controlled agent that discovers outstanding invoices,
evaluates them against user-authored payment policy, and completes a simulated payment
over UCP and AP2. Vocabulary here is derived from the reference payment UI.

## Invoicing

**Invoice**:
A request for payment issued by a Merchant to a Payer, identified to humans by its Doc
Number and carrying a Due Date and a Balance Due.
_Avoid_: Bill, payment request, charge

**Doc Number**:
The human-facing identifier printed on an Invoice (`1022`, `kIV88PDO`). Opaque and not
required to be numeric or sequential.
_Avoid_: Invoice number, invoice ID (that is the system identifier)

**Balance Due**:
The amount still owed on a single Invoice. May be less than the Invoice's original total
when a partial payment has already been applied.
_Avoid_: Total due, amount, outstanding amount

**Outstanding**:
The state of an Invoice whose Balance Due is greater than zero.
_Avoid_: Unpaid, open

**Overdue**:
An Outstanding Invoice whose Due Date has passed.
_Avoid_: Late, past due

**Merchant**:
The business owed money by the Payer. Owns the Invoices and, in this demo, the UCP
surface that exposes them.
_Avoid_: Business, seller, vendor, payee

**Payer**:
The person or organization that owes the Balance Due and on whose behalf the Agent acts.
_Avoid_: Customer, client, buyer, user

**Allowed Payment Methods**:
The set of payment instruments an individual Invoice will accept. Not uniform across a
Merchant's Invoices — some accept bank or card, others card only.

## Agent and policy

**Agent**:
The local, user-controlled runtime that discovers, evaluates, and pays Invoices. Not a
participant in the Merchant's systems.
_Avoid_: Bot, assistant, client

**Policy**:
The deterministic, machine-readable rules the Payer authors in natural language and the
Agent's LLM translates into schema. Evaluated by code, never by the LLM.
_Avoid_: Rules, config, preferences

**Decision**:
The Policy Engine's verdict on one Invoice — ALLOW, DENY, or REQUIRE_APPROVAL — paired
with machine-readable Reason Codes. Durable: a Decision outlives the Agent run that
produced it, and awaits an Approval that may never come.
_Avoid_: Result, outcome, judgement

**Reason Code**:
The machine-readable ground for a Decision (`EXCEEDS_PER_INVOICE_LIMIT`, `NOT_YET_DUE`).
Survives into any Mandate that overrides it.
_Avoid_: Error, message, explanation

**Wake**:
An event that starts an Agent run — an Invoice created, an Approval granted, a scheduler
tick, or a human pressing Run Agent Now. The Agent has no other way to begin.
_Avoid_: Trigger, poll, invocation

**Skill**:
An explicit, named capability the Agent may invoke (Discover Invoices, Evaluate Invoice,
Pay Invoice). Bounds what the Agent is able to do at all.
_Avoid_: Tool, function, action

## The UCP surface

**Discovery Profile**:
The document a Merchant publishes at `/.well-known/ucp` declaring its protocol version,
Capabilities, and the endpoint they are served from. What lets an Agent negotiate with a
Merchant it has never seen before.
_Avoid_: Manifest, config, service descriptor

**Capability**:
A named unit of protocol the Merchant declares it supports (`dev.ucp.shopping.catalog.search`).
An **extension** is a Capability that declares a parent through `extends`.
_Avoid_: Feature, endpoint, API

**Catalog**:
The published Capability through which an Agent searches for what a Merchant offers. Here
what it offers is Invoices — exposed through the Catalog rather than a bespoke endpoint, so
any conforming agent can find them.
_Avoid_: Inventory, product list, search API

**Invoice Extension**:
`com.lapins.demo.invoicing.invoice` — the vendor extension that gives a Catalog product the
meaning of an Invoice. Exposes only Invoice fields, delegates every search to the Invoice
API, and stores nothing.
_Avoid_: Invoice adapter, invoice schema, custom fields

## Payment

**Checkout**:
A single UCP transaction assembling one or more Invoices as line items, each with a
quantity of one. Not the system of record for any Invoice.
_Avoid_: Cart, basket, order

**Mandate**:
The cryptographic proof, bound to a specific Merchant and Checkout, that authorization
was granted. Autonomous Mandates carry only the Policy's authority; Human-Present
Mandates carry an Approval.
_Avoid_: Authorization, token, signature

**Approval**:
A human act admitting a single Invoice to payment despite a Decision of DENY or
REQUIRE_APPROVAL. Distinct from Policy authority, and never performed by the LLM.
_Avoid_: Override, confirmation, sign-off
