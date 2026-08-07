# The Invoice Extension's schema is served from the Merchant, not from lapins.com

UCP's namespace governance is explicit: an entity's schema URL origin **MUST** match the
namespace authority in its name, so `com.lapins.demo.invoicing.invoice` ought to publish
its schema somewhere under `lapins.com`. This demo serves it from the Merchant's own
endpoint instead — `{endpoint}/ucp/schemas/invoice.json` — which a reader checking the
spec will correctly flag as non-conformant.

The rule exists so that a platform fetching a schema knows the party who defined the
extension is the party who served it, and a business cannot publish meaning under a
namespace it does not control. Neither risk is present here: the whole demo runs on one
machine, the Merchant and the extension author are the same person, and there is no
second party to be confused about who said what. Honouring the rule would mean the demo
could not resolve its own extension schema without an internet round trip to a domain
that would have to be kept serving a document for a demo to work offline.

## Considered Options

- **Serve from `lapins.com`** — conformant, and makes the demo depend on the public
  internet and on a host outside this repository to explain its own extension.
- **Advertise a `lapins.com` URL but never fetch it** — conformant on paper, dishonest
  in practice, and the Agent's negotiation step in `intuit-ucp-90m.4` would either break
  or have to pretend to fetch.
- **Serve from the Merchant's endpoint** — chosen. Self-contained, fetchable, and the
  one thing it gives up is a protection against a confusion this demo cannot have.

## Consequences

The extension schema is a real document at a real URL, so the Agent's negotiation can
genuinely fetch and compose it rather than special-casing its own Merchant. The schema
keeps its `$id` and `name` as the reverse-domain identity regardless of where it is
served from, so the identity an Agent keys on is right even though the origin is not.

If any part of this ever ran outside one machine, this is the first thing to change, and
the change is one URL in `discovery_profile.json` plus a host to serve the document that
is already in this repository.
