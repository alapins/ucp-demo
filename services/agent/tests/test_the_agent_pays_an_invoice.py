"""A Wake, and everything that follows from it."""

from conftest import EXTENSION


async def wake(client, because="Run Agent Now"):
    return await client.post("/agent/wake", json={"because": because})


def types(published):
    return [event["type"] for event in published]


def payload_of(published, of_type):
    return next(event["payload"] for event in published if event["type"] == of_type)


async def test_a_wake_carries_the_run_from_discovery_through_to_a_verified_payment(
    client, merchant, agent_window
):
    merchant.holds("inv-1", doc_number="kIV88PDO", balance_due=4300)

    woken = await wake(client)

    assert woken.json() == {
        "woke_because": "Run Agent Now",
        "discovered": 1,
        "paid": 1,
    }
    # The whole story in order, which is what the agent window shows a human.
    assert types(agent_window) == [
        "agent.woke",
        "agent.capabilities_negotiated",
        "agent.invoices_discovered",
        "agent.decided",
        "agent.checkout_opened",
        "agent.payment_completed",
        "agent.payment_verified",
        "agent.finished",
    ]


async def test_the_agent_pays_what_the_merchant_says_is_owed(
    client, merchant, agent_window
):
    merchant.holds("inv-1", balance_due=4300)

    await wake(client)

    assert payload_of(agent_window, "agent.checkout_opened")["amount_minor_units"] == 4300
    completed = payload_of(agent_window, "agent.payment_completed")
    assert completed["amount_minor_units"] == 4300
    assert completed["status"] == "completed"


async def test_payment_is_confirmed_against_the_merchant_not_against_the_checkout(
    client, merchant, agent_window
):
    merchant.holds("inv-1")

    await wake(client)

    # The Invoice has left the Merchant's catalogue, which is the only evidence the
    # Agent accepts that it is settled.
    verified = payload_of(agent_window, "agent.payment_verified")
    assert verified == {"invoice_id": "inv-1", "outstanding": False}


async def test_every_discovered_invoice_gets_a_decision_with_a_reason_code(
    client, merchant, agent_window
):
    merchant.holds("inv-1", doc_number="AAA")
    merchant.holds("inv-2", doc_number="BBB")

    await wake(client)

    decisions = [event for event in agent_window if event["type"] == "agent.decided"]
    assert [event["payload"]["doc_number"] for event in decisions] == ["AAA", "BBB"]
    for event in decisions:
        assert event["payload"]["verdict"] == "ALLOW"
        # The stub Policy names itself as one, rather than passing silently.
        assert event["payload"]["reason_codes"] == ["NO_POLICY_IN_FORCE"]
        # A Decision threads onto the Invoice it is about.
        assert event["correlation_id"] == event["payload"]["invoice_id"]


async def test_a_wake_with_nothing_outstanding_ends_without_paying(
    client, merchant, agent_window
):
    woken = await wake(client, because="scheduler tick")

    assert woken.json() == {"woke_because": "scheduler tick", "discovered": 0, "paid": 0}
    assert types(agent_window) == [
        "agent.woke",
        "agent.capabilities_negotiated",
        "agent.invoices_discovered",
        "agent.finished",
    ]
    assert payload_of(agent_window, "agent.woke") == {"because": "scheduler tick"}


async def test_the_agent_negotiates_before_acting_and_gives_up_on_a_merchant_that_cannot_be_paid(
    client, merchant, agent_window
):
    merchant.holds("inv-1")
    merchant.offers_only("dev.ucp.shopping.catalog.search")

    woken = await wake(client)

    # No Checkout capability means no way to pay, and the Agent says so before it has
    # discovered anything rather than failing partway through a payment.
    assert "dev.ucp.shopping.checkout" in woken.json()["gave_up"]
    assert types(agent_window) == ["agent.woke", "agent.gave_up"]


async def test_the_agent_reports_the_capabilities_it_agreed_on(
    client, merchant, agent_window
):
    await wake(client)

    assert payload_of(agent_window, "agent.capabilities_negotiated")["capabilities"] == [
        "com.lapins.demo.invoicing.invoice",
        "dev.ucp.shopping.catalog.search",
        "dev.ucp.shopping.checkout",
    ]


async def test_an_agent_that_never_understood_invoices_can_still_pay_them(
    client, merchant, agent_window
):
    """The Invoice Extension is a convenience, not a requirement.

    A Merchant offering only the Catalog and Checkout is still payable, because paying
    is done in the protocol's own vocabulary. This is what stops the demo's vendor
    extension from quietly becoming load-bearing.
    """
    merchant.holds("inv-1")
    merchant.offers_only("dev.ucp.shopping.catalog.search", "dev.ucp.shopping.checkout")

    woken = await wake(client)

    assert woken.json()["paid"] == 1
