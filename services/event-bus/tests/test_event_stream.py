from sse import open_stream, past_the_bus_announcing_itself


async def test_an_event_published_by_a_service_reaches_an_open_stream(client):
    async with open_stream(client) as stream:
        await past_the_bus_announcing_itself(stream)
        await client.post(
            "/events",
            json={
                "type": "invoice.created",
                "service": "invoice-api",
                "correlation_id": "corr-1",
                "payload": {"doc_number": "1022"},
            },
        )

        event = await stream.next_event()

    assert event["type"] == "invoice.created"
    assert event["payload"] == {"doc_number": "1022"}


async def test_an_event_published_without_a_correlation_identifier_is_given_one(client):
    async with open_stream(client) as stream:
        await past_the_bus_announcing_itself(stream)
        await client.post(
            "/events",
            json={"type": "service.started", "service": "agent"},
        )

        event = await stream.next_event()

    assert event["service"] == "agent"
    assert event["correlation_id"]


async def test_both_windows_see_the_same_identity_and_time_for_one_event(client):
    async with open_stream(client) as merchant_window, open_stream(client) as agent_window:
        await past_the_bus_announcing_itself(merchant_window)
        await past_the_bus_announcing_itself(agent_window)
        await client.post(
            "/events",
            json={"type": "service.started", "service": "ucp-server"},
        )

        seen_by_merchant = await merchant_window.next_event()
        seen_by_agent = await agent_window.next_event()

    assert seen_by_merchant["id"] == seen_by_agent["id"]
    assert seen_by_merchant["occurred_at"] == seen_by_agent["occurred_at"]


async def test_a_window_sees_the_event_bus_itself_join_the_system(client):
    async with open_stream(client) as window:
        event = await window.next_event()

    assert (event["service"], event["type"]) == ("event-bus", "service.started")


async def test_a_window_opened_after_the_system_started_still_sees_it_start(client):
    await client.post(
        "/events", json={"type": "service.started", "service": "invoice-api"}
    )
    await client.post(
        "/events", json={"type": "service.started", "service": "ucp-server"}
    )

    async with open_stream(client) as window:
        await past_the_bus_announcing_itself(window)
        first = await window.next_event()
        second = await window.next_event()

    assert [first["service"], second["service"]] == ["invoice-api", "ucp-server"]


async def test_a_reconnecting_window_resumes_after_the_last_event_it_saw(client):
    async with open_stream(client) as window:
        await past_the_bus_announcing_itself(window)
        await client.post("/events", json={"type": "demo.ping", "service": "agent"})
        before_the_drop = await window.next_event()

    await client.post("/events", json={"type": "demo.ping", "service": "ucp-server"})

    async with open_stream(client, last_event_id=before_the_drop["id"]) as reconnected:
        first_after_the_drop = await reconnected.next_event()

    assert first_after_the_drop["service"] == "ucp-server"


async def test_the_merchant_window_is_never_sent_the_agents_events(client):
    # The Agent runs on the Payer's infrastructure. The Merchant does not get to
    # watch it think, so these must not reach the merchant window's connection at
    # all — not be delivered and hidden.
    await client.post("/events", json={"type": "agent.woke", "service": "agent"})
    await client.post(
        "/events", json={"type": "invoice.created", "service": "invoice-api"}
    )

    async with open_stream(client, window="merchant") as merchant_window:
        replayed = await merchant_window.next_event()
        await client.post("/events", json={"type": "agent.decided", "service": "agent"})
        await client.post(
            "/events", json={"type": "ucp.checkout_created", "service": "ucp-server"}
        )
        live = await merchant_window.next_event()

    assert replayed["service"] == "invoice-api"
    assert live["service"] == "ucp-server"


async def test_the_agent_window_is_never_sent_the_merchants_events(client):
    await client.post(
        "/events", json={"type": "invoice.created", "service": "invoice-api"}
    )
    await client.post("/events", json={"type": "agent.woke", "service": "agent"})

    async with open_stream(client, window="agent") as agent_window:
        replayed = await agent_window.next_event()
        await client.post(
            "/events", json={"type": "ucp.checkout_created", "service": "ucp-server"}
        )
        await client.post("/events", json={"type": "agent.paid", "service": "agent"})
        live = await agent_window.next_event()

    assert (replayed["service"], replayed["type"]) == ("agent", "agent.woke")
    assert (live["service"], live["type"]) == ("agent", "agent.paid")


async def test_a_stream_asked_for_by_a_name_that_is_not_a_window_is_refused(client):
    refused = await client.get("/events", params={"window": "marchant"})

    # Silently streaming nothing would look exactly like a quiet system, and the
    # demo would appear broken with no clue why.
    assert refused.status_code == 422


async def test_an_idle_stream_keeps_signalling_so_a_window_can_notice_a_drop(bus):
    client = await bus(heartbeat_seconds=0.05)

    async with open_stream(client) as stream:
        await stream.next_heartbeat()
        await stream.next_heartbeat()
