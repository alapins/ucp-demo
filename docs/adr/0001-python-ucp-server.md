# Fork the Python UCP reference server, not the Node one

The rest of this demo's invoice stack is Java, and the UCP overview names the Node.js
reference server as the canonical starting point — so the Python choice will look
arbitrary. It isn't. The Node sample (`samples/rest/nodejs`) contains zero references to
AP2, while the Python sample (`samples/rest/python/server`) composes its checkout from
typed extension mixins supplied by the official `ucp-sdk`, including
`ucp_sdk.models.schemas.shopping.ap2_mandate.Checkout`, and already returns an `ap2`
field in checkout responses. Since AP2 authorization is the point of the demo, starting
from Node would mean hand-writing the mandate schema the Python SDK hands us for free.

## Considered Options

- **Node.js sample (Hono + Zod)** — more test coverage (10 test files vs the Python
  sample's integration tests) and RFC 9421 signing, but no AP2 and no SDK.
- **Rebuild in Java/Spring** — one language across the whole backend, at the cost of
  reimplementing HTTP Message Signatures, the checkout state machine, and the AP2
  mandate schema by hand. Not affordable within the demo's time budget.
- **Python sample (FastAPI + `ucp-sdk`)** — chosen. AP2 mixins, routes generated from
  the spec, an MCP binding, and a matching client sample.

## Consequences

The backend is deliberately polyglot: Java for the Invoice API, Python for the UCP
server and Agent. The Agent is written in Python specifically to share `ucp-sdk` types
with the UCP server, which is the only reason its language isn't a free choice.
