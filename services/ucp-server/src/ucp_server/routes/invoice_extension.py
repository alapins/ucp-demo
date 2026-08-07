"""Serving the Invoice Extension's own schema.

A UCP extension must be self-describing: an Agent that reads `extends` in the
profile then fetches this document to learn how to compose it onto the Catalog
response. The reference server has no equivalent route because every capability
it advertises is published by ucp.dev; a vendor extension has to publish its own.

Namespace governance (overview.md) wants a schema URL whose origin matches the
namespace authority — lapins.com for `com.lapins.*`. A demo that runs entirely on
one machine has no such origin to serve from, so the document is served from the
Merchant's own endpoint and the profile advertises it there.
"""

import json
import pathlib

from fastapi import APIRouter, Request, Response

router = APIRouter()

SCHEMA_TEMPLATE_PATH = pathlib.Path(__file__).parent / "invoice_extension.json"

# The same caching terms the discovery profile is served under: an extension
# schema is every bit as stable and as non-sensitive as the profile pointing at it.
SCHEMA_CACHE_CONTROL = "public, max-age=3600"


@router.get(
    "/ucp/schemas/invoice.json",
    response_model=dict,
    summary="Get Invoice Extension Schema",
)
async def get_invoice_extension_schema(request: Request, response: Response):
    """Return the schema for `com.lapins.demo.invoicing.invoice`."""
    response.headers["Cache-Control"] = SCHEMA_CACHE_CONTROL
    template = SCHEMA_TEMPLATE_PATH.read_text(encoding="utf-8")
    endpoint = str(request.base_url).rstrip("/")
    return json.loads(template.replace("{{ENDPOINT}}", endpoint))
