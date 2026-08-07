"""Checkout, over a Merchant whose line items are Invoices.

This is not the forked `checkout_service.py`, and the difference is deliberate. The
reference implementation prices a Checkout by reading products, inventory and stock
out of its own SQLite — reasonable for a flower shop, which owns what it sells. This
Merchant owns no such thing: an Invoice's Balance Due lives in the Invoice API, and
copying it here to satisfy a checkout engine would quietly make this server a second
system of record. So a Checkout is priced by asking the Invoice API on the way in and
settled by asking it again on the way out, and this module stores only the session
joining those two moments.

A Checkout may carry several Invoices. Each settles as its own payment against its own
Invoice, because that is how the Merchant records them — a Checkout is the Agent's unit
of work, never the Merchant's unit of account.
"""

import uuid

from ucp_sdk.models.schemas.shopping.checkout import Checkout
from ucp_sdk.models.schemas.shopping.types.item import Item
from ucp_sdk.models.schemas.shopping.types.line_item import LineItem
from ucp_sdk.models.schemas.shopping.types.total import Total

# A Checkout's own totals may carry an itemized breakdown, which a line item's cannot,
# so the two are different models under the same name. Imported apart to keep which is
# which visible at the point of use.
from ucp_sdk.models.schemas.shopping.types.totals import Total as CheckoutTotal
from ucp_sdk.models.schemas.ucp import ResponseCatalogSchema

from ucp_server import config
from ucp_server.exceptions import ResourceNotFoundError, UcpError
from ucp_server.invoices import as_invoice

CHECKOUT = "dev.ucp.shopping.checkout"


class NotPayableError(UcpError):
    """Raised when a Checkout names something this Payer cannot pay."""

    def __init__(self, message: str):
        super().__init__(message, code="NOT_PAYABLE", status_code=422)


class AlreadyCompletedError(UcpError):
    """Raised when a Checkout that has already been completed is completed again.

    Not idempotent-success: a second completion would mean a second payment, and the
    caller has to learn that it lost track rather than be told the payment worked.
    """

    def __init__(self, message: str):
        super().__init__(message, code="CHECKOUT_NOT_MODIFIABLE", status_code=409)


class InvoiceCheckout:
    """Assembles Invoices into a Checkout and settles it against the Invoice API."""

    def __init__(self, invoice_api, events):
        self._invoice_api = invoice_api
        self._events = events
        # In memory, and only until the Checkout completes. A Checkout is a transient
        # negotiation about Invoices that are themselves durable elsewhere; persisting
        # it would outlive its usefulness and duplicate state the Merchant already has.
        self._sessions: dict[str, dict] = {}

    async def create(self, payer_email: str, requested_ids: list[str]) -> Checkout:
        """Open a Checkout over the named Invoices, priced at what is owed now."""
        if not requested_ids:
            raise NotPayableError("a Checkout must carry at least one Invoice")

        payable = await self._payable_invoices(payer_email)
        for invoice_id in requested_ids:
            if invoice_id not in payable:
                # Says only that this Payer cannot pay it — an Invoice belonging to
                # somebody else must not be distinguishable from one that never existed.
                raise NotPayableError(
                    f"{invoice_id} is not an Outstanding Invoice of this Payer"
                )

        chosen = [payable[invoice_id] for invoice_id in requested_ids]
        currencies = {record["currency"] for record in chosen}
        if len(currencies) > 1:
            raise NotPayableError(
                "a Checkout cannot mix currencies: " + ", ".join(sorted(currencies))
            )
        currency = currencies.pop()

        checkout_id = f"chk-{uuid.uuid4().hex[:12]}"
        self._sessions[checkout_id] = {
            "payer_email": payer_email,
            "invoice_ids": list(requested_ids),
            "completed": False,
        }

        await self._events.publish(
            "ucp.checkout_created",
            # Correlated on the first Invoice, so a single-Invoice Checkout — which is
            # every Checkout this demo makes — threads onto the story of that Invoice.
            correlation_id=requested_ids[0],
            payload={
                "checkout_id": checkout_id,
                "payer_email": payer_email,
                "invoice_ids": list(requested_ids),
                "amount_minor_units": sum(
                    record["balanceDueMinorUnits"] for record in chosen
                ),
                "currency": currency,
            },
        )
        return self._as_checkout(checkout_id, chosen, currency, status="ready_for_complete")

    async def complete(self, checkout_id: str, payer_email: str) -> Checkout:
        """Settle every Invoice in the Checkout, then report what the Merchant now holds.

        Each Invoice is paid for the whole of its Balance Due. UCP Checkout has no way to
        express a part payment, so offering one is not a decision this server gets to
        make — it asks for the full amount or it does not ask.
        """
        session = self._session(checkout_id, payer_email)
        if session["completed"]:
            raise AlreadyCompletedError(f"Checkout {checkout_id} is already completed")

        payable = await self._payable_invoices(payer_email)
        settled = []
        paid_amounts: dict[str, int] = {}
        for invoice_id in session["invoice_ids"]:
            owed = payable.get(invoice_id)
            if owed is None:
                # Between opening this Checkout and completing it the Invoice stopped
                # being payable — someone else settled it, most likely. Re-reading is
                # the point: the Balance Due at completion is the only one that counts.
                raise NotPayableError(
                    f"{invoice_id} is no longer an Outstanding Invoice of this Payer"
                )
            settling = owed["balanceDueMinorUnits"]
            paid = await self._invoice_api.pay(invoice_id, settling)
            settled.append(paid)
            paid_amounts[invoice_id] = settling
            await self._events.publish(
                "ucp.invoice_settled",
                correlation_id=invoice_id,
                payload={
                    "checkout_id": checkout_id,
                    "invoice_id": invoice_id,
                    "doc_number": paid["docNumber"],
                    "amount_minor_units": owed["balanceDueMinorUnits"],
                    "currency": paid["currency"],
                    "outstanding": paid["outstanding"],
                },
            )

        session["completed"] = True
        await self._events.publish(
            "ucp.checkout_completed",
            correlation_id=session["invoice_ids"][0],
            payload={
                "checkout_id": checkout_id,
                "payer_email": payer_email,
                "invoices_settled": len(settled),
            },
        )
        # Priced from what was actually paid rather than from the Invoices as they now
        # stand: a settled Invoice reports a Balance Due of zero, and a completed
        # Checkout totalling zero would be true of the debt and useless as a receipt.
        return self._as_checkout(
            checkout_id,
            settled,
            settled[0]["currency"],
            status="completed",
            amounts=paid_amounts,
        )

    async def get(self, checkout_id: str, payer_email: str) -> Checkout:
        """A Checkout as it stands, priced against Invoices as they stand."""
        session = self._session(checkout_id, payer_email)
        held = await self._invoice_api.invoices_of(payer_email)
        by_id = {record["id"]: record for record in held}
        carried = [
            by_id[invoice_id]
            for invoice_id in session["invoice_ids"]
            if invoice_id in by_id
        ]
        if not carried:
            raise ResourceNotFoundError(f"no Invoice of Checkout {checkout_id} remains")
        return self._as_checkout(
            checkout_id,
            carried,
            carried[0]["currency"],
            status="completed" if session["completed"] else "ready_for_complete",
        )

    def _session(self, checkout_id: str, payer_email: str) -> dict:
        session = self._sessions.get(checkout_id)
        # A Checkout belonging to another Payer is reported as absent rather than as
        # forbidden, for the same reason an Invoice is.
        if session is None or session["payer_email"] != payer_email:
            raise ResourceNotFoundError(f"no Checkout with id {checkout_id}")
        return session

    async def _payable_invoices(self, payer_email: str) -> dict[str, dict]:
        """This Payer's Outstanding Invoices, by id, read fresh from the Merchant."""
        held = await self._invoice_api.invoices_of(payer_email)
        return {record["id"]: record for record in held if record["outstanding"]}

    def _as_checkout(
        self,
        checkout_id: str,
        records: list[dict],
        currency: str,
        status: str,
        amounts: dict[str, int] | None = None,
    ) -> Checkout:
        """Present the session in UCP's vocabulary."""
        line_items = []
        for record in records:
            invoice = as_invoice(record)
            # A settled Invoice reports a Balance Due of zero, which is true and useless
            # as a line item: what the line was for is what was owed when it was added.
            charged = (
                amounts[record["id"]] if amounts else record["balanceDueMinorUnits"]
            )
            line_items.append(
                LineItem(
                    id=record["id"],
                    item=Item(
                        id=record["id"],
                        title=f"Invoice {invoice.doc_number}",
                        # Minor units alone: unlike the Catalog's Price, a Checkout line
                        # carries no currency of its own, because the Checkout names one
                        # currency for the whole of itself.
                        price=charged,
                    ),
                    # Always one. An Invoice is a particular debt, not a quantity of a
                    # thing, so two of it is not a state the Merchant can represent.
                    quantity=1,
                    totals=[Total(type="subtotal", amount=charged)],
                )
            )

        total = sum(item.totals[0].amount for item in line_items)
        return Checkout(
            ucp=ResponseCatalogSchema(
                version=config.get_server_version(),
                capabilities={CHECKOUT: [{"version": config.get_server_version()}]},
            ),
            id=checkout_id,
            line_items=line_items,
            status=status,
            currency=currency,
            totals=[
                CheckoutTotal(type="subtotal", display_text="Balance Due", amount=total),
                CheckoutTotal(type="total", display_text="Total", amount=total),
            ],
            links=[],
        )
