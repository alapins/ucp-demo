# Overview

I am building a demo showing a local LLM-based agent

- discovering an outstanding invoice
- evaluating it against user-defined payment policies
- autonomously completing a simulated payment.

There is an existing application that allows humans to do the same, the UI for
which is visible
[here](https://connect.intuit.com/t/scs-v1da0f4f3df38d400583eee24fb79f44e1f7d0fc9d3f424b9e9d8fb4ac28f28bb8417b5af0bda6456bafa5c9c0a26a4c2d?locale=en_US&cta=saveAndShareLink).
The demo will expose a rudimentary implementation of the existing invoice
service via UCP and AP2.

Not in scope:

- complete implementation of the invoicing service. Only the parts strictly
  necessary to support the demo flow (based on the reference UI) should be
  implemented.

# Architecture

The demo consists of three primary servers plus a realtime demonstration UI.

                         USER
                          |
                          | Natural-language payment instructions
                          v
                +-----------------------+
                |   Local Agent Server  |
                |                       |
                | LLM                   |
                | Skills                |
                | Policy Engine         |
                | Scheduler             |
                +-----------+-----------+
                            |
                            | UCP
                            v
                +-----------------------+
                |    UCP Server         |
                |                       |
                | UCP Discovery         |
                | Invoice Extension     |
                | Catalog Adapter       |
                | Checkout              |
                | AP2 Authorization     |
                +-----------+-----------+
                            |
                            | Existing private REST API
                            v
                +-----------------------+
                |  Invoice API Server   |
                |                       |
                | Invoice Service       |
                | Payment Simulator     |
                | Event Service         |
                +-----------------------+

All three systems publish activity to a realtime event stream consumed by the
demo UI. They should be constructed as a monorepo in the current directory, and
runnable as a whole system using Docker Compose.

# Invoice API Server

This represents the existing application before UCP is added. It should be built
as a Spring Boot application, using Spring Web, Spring Data JPA, and H2.

It is deliberately minimal and does not understand UCP.

## Invoice Service

Owns the authoritative invoice state. Fields and data model should be derived
from the reference UI.

## Simulated Payment Service

Provides deterministic simulated payment behavior.

Supported outcomes:

success decline

No actual payment credentials or money movement are involved.

# UCP Server

The UCP server is a separate exposure layer placed in front of the existing
Invoice API.

A reference UCP merchant server should be used as the starting point, retaining
its protocol, checkout, validation, payment, and authorization infrastructure.

The UCP server does not become the invoice system of record.

## Invoice Extension

A vendor-defined UCP extension adds invoice-specific meaning to Catalog
resources.

Conceptually:

`com.lapins.demo.invoicing.invoice`

extends the applicable published Catalog capabilities, exposing only invoice
fields and delegating actual search to the Invoice API Server.

## Checkout Service

Uses the published UCP Checkout capability. Invoices are line items with a
quantity of 1.

The delegates to the Invoice API Server for processing of the payment.

## AP2 Authorization Service

Uses the published AP2 mandate extension to represent autonomous authorization.

It verifies that the agent's authorization is cryptographically bound to the
merchant and checkout being executed.

# Local Agent Server

The client represents a user-controlled local agent platform.

It should behave like an OpenClaw-style agent runtime rather than a hard-coded
payment script.

## LLM Orchestrator

The LLM:

Reads the user's natural-language bill-payment instructions. Converts those
instructions into a structured policy. Activates the policy through the
deterministic policy engine. Discovers the merchant's UCP capabilities. Finds
outstanding invoices. Evaluates invoices. Orchestrates checkout and payment.
Verifies the final result. Provides human-readable explanations of its actions.

The LLM cannot directly authorize payment.

## Skill Service

The agent loads explicit skills defining how it may interact with the invoicing
system.

Minimum skills:

### Configure Payment Policy

Converts natural-language instructions into the policy-engine schema.

Example:

Pay Demo Merchant invoices automatically when they are due within three days.
Never pay more than $500. Always pay the complete outstanding balance.

### Discover Invoices

Uses the UCP profile, Catalog capabilities, and invoice extension to retrieve
outstanding invoices.

### Evaluate Invoice

Passes authoritative invoice facts to the deterministic policy engine.

The LLM may not override the engine's result.

### Pay Invoice

Creates and verifies the UCP checkout, AP2 authorization, and simulated payment.

### Verify Payment

Retrieves authoritative state after payment and confirms that the invoice is
paid.

## Policy Engine

The LLM creates policy; deterministic code evaluates it.

Example generated policy:

{ "merchant": "demo_merchant", "pay_when_due_within_days": 3,
"maximum_single_payment": 50000, "currency": "USD", "full_balance_only": true }

For each invoice, the engine returns:

ALLOW DENY REQUIRE_APPROVAL

with machine-readable reason codes.

Checkout completion is impossible unless the current result is ALLOW.

## Scheduler and Event Listener

The agent discovers invoices through two mechanisms.

Event-driven: an invoice event wakes the agent immediately.

Scheduled: the agent periodically searches UCP for outstanding invoices.

A manual Run Agent Now action is also provided for demonstration reliability.

# Logging/Reporting

There should be a single server exposing events through SSE. Significant events,
including invoice creation, payment, and decision results (AP2 mandate
verification) should be exposed. This will allow the UI to subscribe to the
events to track the stages each action results in.
