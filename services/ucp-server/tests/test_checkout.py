"""Paying Invoices through Checkout, which is what this Merchant's Checkout is for."""

from conftest import ADA, ADAS_KEY, GRACE, GRACES_KEY
from invoices import as_the_invoice_api_reports_it


async def open_checkout(client, *invoice_ids, api_key=ADAS_KEY):
    return await client.post(
        "/checkout",
        json={"line_items": [{"item": {"id": id}, "quantity": 1} for id in invoice_ids]},
        headers={"X-API-Key": api_key},
    )


async def complete(client, checkout_id, api_key=ADAS_KEY):
    return await client.post(
        f"/checkout/{checkout_id}/complete", json={}, headers={"X-API-Key": api_key}
    )


async def search(client, api_key=ADAS_KEY):
    return await client.post(
        "/catalog/search", json={}, headers={"X-API-Key": api_key}
    )


def published(events, of_type):
    return [event for event in events if event["type"] == of_type]


async def test_a_checkout_is_priced_at_the_balance_due_not_the_original_total(
    client, invoice_api
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1",
            payer_email=ADA,
            original_total_minor_units=20000,
            balance_due_minor_units=12500,
        ),
        against=ADA,
    )

    opened = await open_checkout(client, "inv-1")

    assert opened.status_code == 201
    checkout = opened.json()
    assert checkout["status"] == "ready_for_complete"
    assert checkout["currency"] == "USD"
    assert [total["amount"] for total in checkout["totals"]] == [12500, 12500]
    line_item = checkout["line_items"][0]
    # An Invoice is a particular debt, so the only quantity it can have is one.
    assert line_item["quantity"] == 1
    assert line_item["item"]["price"] == 12500


async def test_completing_a_checkout_settles_the_invoice_at_the_system_of_record(
    client, invoice_api
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1", doc_number="kIV88PDO", payer_email=ADA, balance_due_minor_units=4300
        ),
        against=ADA,
    )
    checkout_id = (await open_checkout(client, "inv-1")).json()["id"]

    completed = await complete(client, checkout_id)

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    # Read back from the Merchant rather than from the response: the Invoice is settled
    # because the system of record says so, not because Checkout reported success.
    assert (await search(client)).json()["products"] == []


async def test_a_checkout_may_carry_several_invoices_each_settled_in_its_own_right(
    client, invoice_api, merchant_window
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1", doc_number="AAA", payer_email=ADA, balance_due_minor_units=4300
        ),
        as_the_invoice_api_reports_it(
            id="inv-2", doc_number="BBB", payer_email=ADA, balance_due_minor_units=1200
        ),
        against=ADA,
    )
    checkout_id = (await open_checkout(client, "inv-1", "inv-2")).json()["id"]

    completed = await complete(client, checkout_id)

    assert [total["amount"] for total in completed.json()["totals"]] == [5500, 5500]
    settled = published(merchant_window, "ucp.invoice_settled")
    assert [event["payload"]["doc_number"] for event in settled] == ["AAA", "BBB"]
    # Each Invoice threads onto its own story, not onto the Checkout's.
    assert [event["correlation_id"] for event in settled] == ["inv-1", "inv-2"]
    assert (await search(client)).json()["products"] == []


async def test_the_full_balance_due_is_paid_and_no_partial_amount_is_proposed(
    client, invoice_api, merchant_window
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1",
            payer_email=ADA,
            original_total_minor_units=20000,
            balance_due_minor_units=12500,
        ),
        against=ADA,
    )
    checkout_id = (await open_checkout(client, "inv-1")).json()["id"]

    await complete(client, checkout_id)

    settled = published(merchant_window, "ucp.invoice_settled")[0]["payload"]
    assert settled["amount_minor_units"] == 12500
    assert settled["outstanding"] is False


async def test_a_checkout_cannot_be_completed_twice(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(id="inv-1", payer_email=ADA), against=ADA
    )
    checkout_id = (await open_checkout(client, "inv-1")).json()["id"]
    await complete(client, checkout_id)

    again = await complete(client, checkout_id)

    # A second completion would mean a second payment, so the caller is told it lost
    # track rather than being told the payment worked.
    assert again.status_code == 409
    assert again.json()["messages"][0]["code"] == "CHECKOUT_NOT_MODIFIABLE"


async def test_a_payer_cannot_check_out_another_payers_invoice(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(id="inv-grace", payer_email=GRACE), against=GRACE
    )

    refused = await open_checkout(client, "inv-grace", api_key=ADAS_KEY)

    assert refused.status_code == 422
    assert refused.json()["messages"][0]["code"] == "NOT_PAYABLE"


async def test_a_settled_invoice_cannot_be_checked_out(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1", payer_email=ADA, balance_due_minor_units=0, outstanding=False
        ),
        against=ADA,
    )

    refused = await open_checkout(client, "inv-1")

    assert refused.status_code == 422


async def test_a_checkout_settled_by_someone_else_first_is_refused_at_completion(
    client, invoice_api
):
    invoice_api.holds(
        as_the_invoice_api_reports_it(
            id="inv-1", payer_email=ADA, balance_due_minor_units=4300
        ),
        against=ADA,
    )
    checkout_id = (await open_checkout(client, "inv-1")).json()["id"]
    # Somebody pays it by hand in the gap between opening and completing.
    await client.post(
        "/checkout", json={"line_items": []}, headers={"X-API-Key": ADAS_KEY}
    )
    settled_elsewhere = (await open_checkout(client, "inv-1")).json()["id"]
    await complete(client, settled_elsewhere)

    refused = await complete(client, checkout_id)

    assert refused.status_code == 422
    assert refused.json()["messages"][0]["code"] == "NOT_PAYABLE"


async def test_another_payers_checkout_is_reported_as_absent(client, invoice_api):
    invoice_api.holds(
        as_the_invoice_api_reports_it(id="inv-1", payer_email=ADA), against=ADA
    )
    checkout_id = (await open_checkout(client, "inv-1")).json()["id"]

    looked_for = await client.get(
        f"/checkout/{checkout_id}", headers={"X-API-Key": GRACES_KEY}
    )

    assert looked_for.status_code == 404
