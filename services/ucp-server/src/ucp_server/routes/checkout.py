"""The Checkout endpoints, at the paths the published REST binding names.

`POST /checkout` and `POST /checkout/{id}/complete` are what an Agent will try after
reading `dev.ucp.shopping.checkout` out of the Discovery Profile, so they are served
where the profile promises them rather than where this demo would have found convenient.
"""

from fastapi import APIRouter, Body, Header
from ucp_sdk.models.schemas.shopping.checkout import Checkout
from ucp_sdk.models.schemas.shopping.checkout_create_request import (
    CheckoutCreateRequest,
)

from ucp_server.payers import Payers
from ucp_server.services.invoice_checkout import InvoiceCheckout


def checkout_router(checkout: InvoiceCheckout, payers: Payers) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/checkout",
        response_model=Checkout,
        response_model_exclude_none=True,
        operation_id="create_checkout",
        summary="Create Checkout",
        status_code=201,
    )
    async def create_checkout(
        body: CheckoutCreateRequest,
        x_api_key: str = Header(None, alias="X-API-Key"),
    ) -> Checkout:
        """Open a Checkout over the Invoices its line items name.

        A line item's `item.id` is the Invoice's id, which is what Catalog Search
        published as the product and variant id — so an Agent checks out exactly what
        it discovered, with nothing to translate in between.
        """
        return await checkout.create(
            payers.identified_by(x_api_key),
            [line.item.id for line in body.line_items],
        )

    @router.get(
        "/checkout/{checkout_id}",
        response_model=Checkout,
        response_model_exclude_none=True,
        operation_id="get_checkout",
        summary="Get Checkout",
    )
    async def get_checkout(
        checkout_id: str,
        x_api_key: str = Header(None, alias="X-API-Key"),
    ) -> Checkout:
        return await checkout.get(checkout_id, payers.identified_by(x_api_key))

    @router.post(
        "/checkout/{checkout_id}/complete",
        response_model=Checkout,
        response_model_exclude_none=True,
        operation_id="complete_checkout",
        summary="Complete Checkout",
    )
    async def complete_checkout(
        checkout_id: str,
        body: dict = Body(default_factory=dict),
        x_api_key: str = Header(None, alias="X-API-Key"),
    ) -> Checkout:
        """Settle the Checkout, delegating payment to the Merchant's own system.

        The body is read and ignored. UCP carries payment details here, and this demo's
        only handler is the mock one the Discovery Profile declares: settlement is
        simulated inside the Invoice API, so there is nothing for a processor to be told.
        """
        del body  # Unused.
        return await checkout.complete(checkout_id, payers.identified_by(x_api_key))

    return router
