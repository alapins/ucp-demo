"""Searching the Catalog, which is this Merchant's Invoices."""

from conftest import ADA, ADAS_KEY, GRACE, GRACES_KEY
from invoices import as_the_invoice_api_reports_it

EXTENSION = "com.lapins.demo.invoicing.invoice"


async def search(client, api_key=ADAS_KEY, **body):
    return await client.post(
        "/catalog/search",
        json=body or {"query": "outstanding invoices"},
        headers={"X-API-Key": api_key},
    )


async def test_a_search_returns_the_payers_invoices_as_the_invoice_api_reports_them(
    client, invoice_api
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            doc_number="kIV88PDO",
            payer_email=ADA,
            original_total_minor_units=20000,
            balance_due_minor_units=12500,
            currency="USD",
            due_date="2026-08-14",
            overdue=False,
            allowed_payment_methods=("CARD",),
        ),
        against=ADA,
    )

    found = await search(client)

    invoice = found.json()["products"][0][EXTENSION]
    assert invoice == {
        "doc_number": "kIV88PDO",
        "due_date": "2026-08-14",
        "balance_due": {"amount": 12500, "currency": "USD"},
        "original_total": {"amount": 20000, "currency": "USD"},
        "outstanding": True,
        "overdue": False,
        "allowed_payment_methods": ["CARD"],
        "merchant": {
            "name": "Demo Merchant",
            "contact_email": "billing@demo-merchant.example",
            "payment_instructions": "Please pay by the due date.",
        },
        "payer": {"email": ADA},
    }


def doc_numbers(found):
    return [product[EXTENSION]["doc_number"] for product in found.json()["products"]]


async def test_the_api_key_decides_whose_invoices_come_back(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(doc_number="ADA-1", payer_email=ADA), against=ADA
    )
    invoice_api.holds(
        as_the_invoice_api_reports_it(doc_number="GRACE-1", payer_email=GRACE),
        against=GRACE,
    )

    assert doc_numbers(await search(client, api_key=ADAS_KEY)) == ["ADA-1"]
    assert doc_numbers(await search(client, api_key=GRACES_KEY)) == ["GRACE-1"]


async def test_a_search_carrying_no_api_key_is_refused(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(doc_number="ADA-1", payer_email=ADA), against=ADA
    )

    refused = await client.post("/catalog/search", json={})

    # 401 rather than an empty result: an Agent that lost its key must be able to
    # tell "you are nobody" from "you owe nothing".
    assert refused.status_code == 401
    assert refused.json()["ucp"]["status"] == "error"


async def test_a_search_carrying_an_unrecognised_api_key_is_refused(client):
    refused = await search(client, api_key="not-a-key-anyone-issued")

    assert refused.status_code == 401


async def test_a_settled_invoice_is_not_in_the_catalogue(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            doc_number="PAID-1",
            payer_email=ADA,
            balance_due_minor_units=0,
            outstanding=False,
        ),
        as_the_invoice_api_reports_it(doc_number="OWED-1", payer_email=ADA),
        against=ADA,
    )

    assert doc_numbers(await search(client)) == ["OWED-1"]


async def test_a_search_reports_what_the_invoice_api_says_now_not_what_it_said(
    client, invoice_api
):
    # The exposure layer stores nothing, so a Balance Due the Merchant just changed
    # cannot come back stale — there is nowhere for a stale copy to live.
    invoice_api.holds(
        as_the_invoice_api_reports_it(payer_email=ADA, balance_due_minor_units=12500),
        against=ADA,
    )
    before = await search(client)

    invoice_api.holds(
        as_the_invoice_api_reports_it(payer_email=ADA, balance_due_minor_units=2500),
        against=ADA,
    )
    after = await search(client)

    assert before.json()["products"][0][EXTENSION]["balance_due"]["amount"] == 12500
    assert after.json()["products"][0][EXTENSION]["balance_due"]["amount"] == 2500


async def test_an_agent_that_ignores_the_extension_still_sees_a_payable_product(
    client, invoice_api
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            doc_number="kIV88PDO",
            payer_email=ADA,
            original_total_minor_units=20000,
            balance_due_minor_units=12500,
        ),
        against=ADA,
    )

    product = (await search(client)).json()["products"][0]

    # Priced at the Balance Due, not the original total: an Agent reading only the
    # base capability must not be led into overpaying a part-paid Invoice.
    assert product["price_range"]["min"] == {"amount": 12500, "currency": "USD"}
    assert product["variants"][0]["price"] == {"amount": 12500, "currency": "USD"}
    assert product["title"] == "Invoice kIV88PDO"


async def test_the_merchant_window_sees_the_ucp_server_answer_a_search(
    client, invoice_api, merchant_window
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(payer_email=ADA), against=ADA
    )

    await search(client)

    searched = [
        event for event in merchant_window if event["type"] == "ucp.catalog_searched"
    ]
    # Labelled as the exposure layer's own doing, so an operator can tell it from
    # the system of record's activity in the same stream.
    assert [event["service"] for event in searched] == ["ucp-server"]
    assert searched[0]["payload"]["invoices_returned"] == 1


async def test_a_search_reports_a_silent_invoice_api_rather_than_an_empty_catalogue(
    client, invoice_api, merchant_window
):
    invoice_api.is_down()

    failed = await search(client)

    # "No Invoices" and "I could not ask" must not look alike: an Agent told the
    # former concludes there is nothing to pay and goes back to sleep.
    assert failed.status_code == 502
    assert failed.json()["messages"][0]["code"] == "INVOICE_API_UNAVAILABLE"
    assert not [
        event for event in merchant_window if event["type"] == "ucp.catalog_searched"
    ]
