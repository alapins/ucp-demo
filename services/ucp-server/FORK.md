# This server is a fork

`src/ucp_server/` is forked from the UCP Python reference merchant server, per
[ADR 0001](../../docs/adr/0001-python-ucp-server.md).

| | |
| --- | --- |
| Upstream | https://github.com/Universal-Commerce-Protocol/samples |
| Path | `rest/python/server` |
| Commit | `6ea866b9c5b7a6a97629b6aea22eb3b0eac4cdcb` (2026-08-05) |
| Licence | Apache 2.0 — headers retained on every forked file |

## Forked as-is

`db.py`, `dependencies.py`, `enums.py`, `exceptions.py`, `ucp_signing.py`,
`ucp_version.py`, `generated_routes/ucp_routes.py`, `routes/mcp.py`,
`routes/order.py`, `routes/ucp_implementation.py`,
`services/checkout_service.py`, `services/fulfillment_service.py`.

The only edit is to imports. The reference server is laid out to be run as a
script, so its modules import each other flatly (`import db`); here they are a
package, so those became `from ucp_server import db`. Nothing else was touched,
which is what makes upstream changes still readable as diffs.

Checkout, signing and the AP2 machinery are forked but not yet wired into
`app.py`. They arrive with the tickets that need them — Checkout in
`intuit-ucp-90m.7`, Mandate verification in `.8` — and forking them now means
that work adapts one tree rather than fetching a second copy of it.

## Changed for this demo

**`config.py`** — the reference reads settings from absl command-line flags,
which suits a sample you launch by hand. This demo is started by Docker Compose,
so the same settings are read from the environment. The attribute names are
unchanged, so vendored code reading `config.FLAGS.x` needed no edit.

**`routes/discovery_profile.json`** — this Merchant's profile rather than the
flower shop's: Catalog Search and Checkout, the `com.lapins.demo.invoicing.invoice`
extension, and the mock payment handler. Shopify and Google Pay handlers dropped,
since no real payment processor is in scope.

**`models.py`** — gained `InvoiceProduct` and `InvoiceSearchResponse`, composing
the Invoice extension onto the SDK's catalog models the way the reference
composes `UnifiedCheckout` from its extension mixins.

**`server.py` → `app.py`** — the reference's absl `main()` and uvicorn launch are
replaced by an application factory, so tests can build a server without a
process, and so the Event Bus publisher and Invoice API client are constructed
once and injected rather than reached for globally.

## Not forked

`import_csv.py`, `dump_*.py`, `test_data/`, and the flower-shop CSVs: they load
and inspect a product catalogue, and this Merchant has no products. Its
catalogue is Invoices, read live from the Invoice API on every search.

The reference's own tests (`integration_test.py`, `signature_integration_test.py`,
`ucp_signing_test.py`) are not forked either — they test the flower shop. Their
integration-test style is nevertheless the model for `tests/`, and their signing
tests are the pattern to follow for Mandate verification in `.8`.

## Deliberately absent from `db.py`

The reference keeps products, promotions, inventory, discounts and shipping rates
in SQLite because a flower shop owns its inventory. Those tables are still in the
forked file — `services/checkout_service.py` reads them — but nothing in this
demo writes an Invoice fact to them, and nothing may: the Invoice API is the sole
system of record. `.7` strips what Checkout turns out not to need.
