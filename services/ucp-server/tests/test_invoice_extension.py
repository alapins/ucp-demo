"""The vendor extension that gives Catalog resources Invoice meaning."""

EXTENSION = "com.lapins.demo.invoicing.invoice"


async def _declaration(client):
    profile = (await client.get("/.well-known/ucp")).json()
    return profile["ucp"]["capabilities"][EXTENSION][0]


async def test_the_extension_hangs_off_the_published_catalog_capability(client):
    profile = (await client.get("/.well-known/ucp")).json()
    capabilities = profile["ucp"]["capabilities"]

    # An extension is only meaningful if its parent is advertised too, so an Agent
    # that ignores the extension can still search the Catalog and get products.
    assert "dev.ucp.shopping.catalog.search" in capabilities
    assert capabilities[EXTENSION][0]["extends"] == "dev.ucp.shopping.catalog.search"


async def test_the_advertised_schema_can_be_fetched_and_names_its_parent(client):
    declaration = await _declaration(client)

    schema = (await client.get(declaration["schema"])).json()

    assert schema["name"] == EXTENSION
    # Deterministic schema resolution (overview.md, Extension Schema Pattern): the
    # $defs key is the parent's full capability name, so `extends` maps straight to
    # the composition an Agent must apply.
    assert declaration["extends"] in schema["$defs"]


async def test_the_extension_adds_invoice_fields_and_nothing_else(client):
    declaration = await _declaration(client)

    schema = (await client.get(declaration["schema"])).json()

    # Money carries its own currency, as everywhere else in UCP, so the Invoice's
    # currency travels inside balance_due and original_total rather than beside
    # them where the two could disagree.
    assert set(schema["$defs"]["invoice"]["properties"]) == {
        "doc_number",
        "due_date",
        "balance_due",
        "original_total",
        "outstanding",
        "overdue",
        "allowed_payment_methods",
        "merchant",
        "payer",
    }
