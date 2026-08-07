"""The Merchant's invoicing system, reached over its own private REST API.

This is the only place the UCP Server learns anything about an Invoice. There is
no cache and no local copy: every Catalog search asks the Invoice API again, so
an Invoice the Merchant just changed cannot be reported here as it used to be.
"""

import httpx

from ucp_server.exceptions import UcpError


class InvoiceApiUnavailableError(UcpError):
    """Raised when the system of record cannot be reached or refuses to answer.

    A 502 rather than a 500: the failure is behind this server, and an Agent that
    knows the difference can retry rather than give up on the Merchant.
    """

    def __init__(self, message: str):
        super().__init__(message, code="INVOICE_API_UNAVAILABLE", status_code=502)


class PaymentRefusedError(UcpError):
    """Raised when the system of record declines to apply a payment.

    A 422: the Invoice exists and the caller may pay it, but its state does not admit
    this payment — already settled, or the amount is not one it will take.
    """

    def __init__(self, message: str):
        super().__init__(message, code="PAYMENT_REFUSED", status_code=422)


class InvoiceApi:
    """Reads Invoices from the system of record, and asks it to settle them."""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def invoices_of(self, payer_email: str) -> list[dict]:
        """Every Invoice the Merchant holds against one Payer.

        Scoping happens here, in the request, rather than by filtering a full list
        afterwards — a Payer's Invoices should never travel over a wire on the way
        to answering somebody else.
        """
        try:
            answered = await self._client.get(
                "/invoices", params={"payerEmail": payer_email}
            )
            answered.raise_for_status()
        except httpx.HTTPError as unreachable:
            raise InvoiceApiUnavailableError(
                f"the Invoice API did not answer: {unreachable}"
            ) from unreachable
        return answered.json()

    async def pay(self, invoice_id: str, amount_minor_units: int) -> dict:
        """Settle an Invoice, and report it as the system of record now holds it.

        Settlement is the Merchant's act, not this server's: all that happens here is
        that the Invoice API is asked. What comes back is its answer, not a local
        assumption about what the answer should have been.
        """
        try:
            answered = await self._client.post(
                f"/invoices/{invoice_id}/payments",
                json={"amountMinorUnits": amount_minor_units},
            )
            answered.raise_for_status()
        except httpx.HTTPStatusError as refused:
            # The Invoice API refusing a payment is a fact about the Invoice, not an
            # outage, and an Agent must be able to tell those apart.
            raise PaymentRefusedError(
                f"the Invoice API refused the payment: {refused.response.text}"
            ) from refused
        except httpx.HTTPError as unreachable:
            raise InvoiceApiUnavailableError(
                f"the Invoice API did not answer: {unreachable}"
            ) from unreachable
        return answered.json()

    async def aclose(self) -> None:
        await self._client.aclose()
