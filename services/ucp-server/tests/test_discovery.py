"""What an Agent that has never seen this Merchant before can find out."""

UCP_VERSION = "2026-04-08"


async def test_an_agent_learns_the_protocol_version_and_where_to_call(client):
    profile = (await client.get("/.well-known/ucp")).json()

    ucp = profile["ucp"]
    rest = next(
        service
        for service in ucp["services"]["dev.ucp.shopping"]
        if service["transport"] == "rest"
    )
    assert ucp["version"] == UCP_VERSION
    # The endpoint is the address the Agent reached us on, not a configured guess,
    # so the profile stays right whether the demo runs under Compose or on a laptop.
    assert rest["endpoint"] == "http://merchant.test"
    assert rest["version"] == UCP_VERSION
