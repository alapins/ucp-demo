"""The Merchant, as the Agent is able to reach it.

Every fact the Agent holds about an Invoice arrives through this module, and nothing
arrives any other way — there is no back channel to the Invoice API and no local store
of what an Invoice used to say. That is what makes "the Agent never acts on a figure it
inferred" checkable rather than merely intended: the only figures it has are these.

The Agent finds its way in by reading the Discovery Profile, not by being told paths.
The endpoint it posts to is the one the Merchant published, so a Merchant that moved its
REST binding would still be reachable without changing anything here.
"""

import httpx

CATALOG_SEARCH = "dev.ucp.shopping.catalog.search"
CHECKOUT = "dev.ucp.shopping.checkout"
INVOICE_EXTENSION = "com.lapins.demo.invoicing.invoice"

# What the Agent must find on offer before it will act. A Merchant publishing less than
# this cannot be shopped by this Agent, and saying so up front is better than failing
# halfway through a payment.
REQUIRED = (CATALOG_SEARCH, CHECKOUT)


class CannotNegotiate(Exception):
    """The Merchant does not offer what the Agent needs to do its work."""


class Merchant:
    """One Merchant's UCP surface."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self._client = httpx.AsyncClient(
            base_url=base_url, timeout=timeout, headers={"X-API-Key": api_key}
        )
        self._endpoint: str | None = None

    async def negotiate(self) -> list[str]:
        """Read the Discovery Profile and agree what both sides can do.

        Returns the intersection of what the Merchant offers and what this Agent
        understands, and refuses outright if that intersection is missing anything the
        Agent needs. The Invoice Extension is deliberately *not* required: an Agent that
        can read a Catalog product can pay an Invoice without ever understanding what an
        Invoice is, and requiring the extension would make this Agent less general than
        the protocol it speaks.
        """
        found = await self._client.get("/.well-known/ucp")
        found.raise_for_status()
        profile = found.json()["ucp"]

        offered = set(profile.get("capabilities", {}))
        missing = [capability for capability in REQUIRED if capability not in offered]
        if missing:
            raise CannotNegotiate(
                "the Merchant does not offer " + ", ".join(sorted(missing))
            )

        # The path the Merchant says to use, rather than one this Agent assumed.
        rest = [
            service
            for service in profile.get("services", {}).get("dev.ucp.shopping", [])
            if service.get("transport") == "rest"
        ]
        if not rest:
            raise CannotNegotiate("the Merchant publishes no REST binding for shopping")
        self._endpoint = rest[0]["endpoint"].rstrip("/")

        understood = set(REQUIRED) | {INVOICE_EXTENSION}
        return sorted(offered & understood)

    async def outstanding_invoices(self) -> list[dict]:
        """Search the Catalog, which for this Merchant is its Invoices."""
        found = await self._client.post(
            self._at("/catalog/search"), json={"query": "outstanding invoices"}
        )
        found.raise_for_status()
        return found.json()["products"]

    async def open_checkout(self, invoice_ids: list[str]) -> dict:
        """Assemble the named Invoices into one Checkout, each a line of quantity one."""
        opened = await self._client.post(
            self._at("/checkout"),
            json={
                "line_items": [
                    {"item": {"id": invoice_id}, "quantity": 1}
                    for invoice_id in invoice_ids
                ]
            },
        )
        opened.raise_for_status()
        return opened.json()

    async def complete_checkout(self, checkout_id: str) -> dict:
        """Settle a Checkout. The Merchant's own systems do the paying."""
        completed = await self._client.post(
            self._at(f"/checkout/{checkout_id}/complete"), json={}
        )
        completed.raise_for_status()
        return completed.json()

    def _at(self, path: str) -> str:
        if self._endpoint is None:
            # Reaching a Merchant before negotiating with it means guessing at paths,
            # which is the thing discovery exists to stop.
            raise CannotNegotiate("negotiate with the Merchant before calling it")
        return f"{self._endpoint}{path}"

    async def aclose(self) -> None:
        await self._client.aclose()
