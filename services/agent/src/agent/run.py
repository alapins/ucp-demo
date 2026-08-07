"""One Agent run: the whole cycle from being woken to having paid.

A run is started by a Wake and always ends — it never waits for anybody. Per ADR 0002
that is what lets a single mechanism serve every trigger the Agent has, and what stops a
human's hesitation from becoming a hung Agent on screen.

Each step publishes as it happens rather than the run reporting at the end, because the
agent window is watching a process, not reading a summary. The correlation identifier is
the Invoice's own id throughout, so the story told here joins the one the Merchant's
services are telling about the same Invoice.
"""

import asyncio

from agent import policy
from agent.merchant import CannotNegotiate, Merchant

INVOICE_EXTENSION = "com.lapins.demo.invoicing.invoice"


class AgentRun:
    """Discovers Invoices, decides about them, and pays the ones it may."""

    def __init__(self, merchant: Merchant, events):
        self._merchant = merchant
        self._events = events
        # One run at a time. The Agent has four ways to be woken and they can arrive
        # together — a human pressing the button while an Invoice-created Wake is in
        # flight. Two runs overlapping would each discover the same Invoice and the
        # second would be refused at completion, which reads on screen as a broken
        # Agent rather than as the double payment it correctly prevented.
        self._one_run_at_a_time = asyncio.Lock()

    async def wake(self, because: str) -> dict:
        """Run once, and report what happened.

        The return value is for whoever pressed the button; the events are the demo.
        """
        async with self._one_run_at_a_time:
            return await self._run(because)

    async def _run(self, because: str) -> dict:
        await self._events.publish("agent.woke", payload={"because": because})

        try:
            agreed = await self._merchant.negotiate()
        except CannotNegotiate as refused:
            await self._events.publish(
                "agent.gave_up", payload={"because": str(refused)}
            )
            return {"woke_because": because, "gave_up": str(refused)}

        await self._events.publish(
            "agent.capabilities_negotiated", payload={"capabilities": agreed}
        )

        discovered = await self._merchant.outstanding_invoices()
        await self._events.publish(
            "agent.invoices_discovered",
            payload={
                "count": len(discovered),
                "invoices": [_summarise(product) for product in discovered],
            },
        )
        if not discovered:
            await self._events.publish("agent.finished", payload={"paid": 0})
            return {"woke_because": because, "discovered": 0, "paid": 0}

        allowed = []
        for product in discovered:
            decision = policy.decide(product["id"], _invoice_of(product))
            await self._events.publish(
                "agent.decided",
                correlation_id=decision.invoice_id,
                payload={
                    "invoice_id": decision.invoice_id,
                    "doc_number": decision.doc_number,
                    "verdict": decision.verdict,
                    "reason_codes": list(decision.reason_codes),
                },
            )
            if decision.is_allowed:
                allowed.append(decision)

        if not allowed:
            await self._events.publish("agent.finished", payload={"paid": 0})
            return {"woke_because": because, "discovered": len(discovered), "paid": 0}

        paid = await self._pay(allowed)
        await self._events.publish("agent.finished", payload={"paid": len(paid)})
        return {
            "woke_because": because,
            "discovered": len(discovered),
            "paid": len(paid),
        }

    async def _pay(self, allowed: list[policy.Decision]) -> list[str]:
        """Check out every Invoice a Decision allowed, then confirm it really is settled."""
        invoice_ids = [decision.invoice_id for decision in allowed]
        checkout = await self._merchant.open_checkout(invoice_ids)
        await self._events.publish(
            "agent.checkout_opened",
            correlation_id=invoice_ids[0],
            payload={
                "checkout_id": checkout["id"],
                "invoice_ids": invoice_ids,
                "amount_minor_units": _total_of(checkout),
                "currency": checkout["currency"],
            },
        )

        completed = await self._merchant.complete_checkout(checkout["id"])
        await self._events.publish(
            "agent.payment_completed",
            correlation_id=invoice_ids[0],
            payload={
                "checkout_id": completed["id"],
                "status": completed["status"],
                "amount_minor_units": _total_of(completed),
                "currency": completed["currency"],
            },
        )

        await self._verify(invoice_ids)
        return invoice_ids

    async def _verify(self, invoice_ids: list[str]) -> None:
        """Re-read the Merchant's own account of the Invoices.

        The Agent does not take a completed Checkout as proof of payment. It asks the
        Merchant what it now holds, and an Invoice that has left the Catalog is settled
        because the system of record says so — the one claim in this run that does not
        depend on the Agent's own view of what it did.
        """
        still_outstanding = {
            product["id"] for product in await self._merchant.outstanding_invoices()
        }
        for invoice_id in invoice_ids:
            settled = invoice_id not in still_outstanding
            await self._events.publish(
                "agent.payment_verified" if settled else "agent.payment_unconfirmed",
                correlation_id=invoice_id,
                payload={"invoice_id": invoice_id, "outstanding": not settled},
            )


def _invoice_of(product: dict) -> dict:
    """The Invoice inside a Catalog product, or the product itself if unextended."""
    return product.get(INVOICE_EXTENSION) or product


def _summarise(product: dict) -> dict:
    """Enough of an Invoice for a human watching the window to recognise it."""
    invoice = _invoice_of(product)
    balance = invoice.get("balance_due") or {}
    return {
        "invoice_id": product["id"],
        "doc_number": invoice.get("doc_number"),
        "due_date": invoice.get("due_date"),
        "balance_due_minor_units": balance.get("amount"),
        "currency": balance.get("currency"),
        "overdue": invoice.get("overdue"),
    }


def _total_of(checkout: dict) -> int | None:
    for total in checkout.get("totals", []):
        if total.get("type") == "total":
            return total.get("amount")
    return None
