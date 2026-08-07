"""The Catalog capability, over a Merchant whose catalogue is Invoices.

Search does no matching of its own. It asks the Invoice API for the Payer's
Invoices and presents them; the Merchant's system of record decides what exists
and what it is worth, exactly as it does for the humans who pay by hand.
"""

from ucp_sdk.models.schemas.shopping.types.description import Description
from ucp_sdk.models.schemas.shopping.types.price_range import PriceRange
from ucp_sdk.models.schemas.shopping.types.variant import Availability, Variant
from ucp_sdk.models.schemas.ucp import ResponseCatalogSchema

from ucp_server import config
from ucp_server.invoices import as_invoice
from ucp_server.models import InvoiceProduct, InvoiceSearchResponse

CATALOG_SEARCH = "dev.ucp.shopping.catalog.search"
INVOICE_EXTENSION = "com.lapins.demo.invoicing.invoice"


class CatalogService:
    """Answers Catalog searches out of the Merchant's Invoices."""

    def __init__(self, invoice_api, events):
        self._invoice_api = invoice_api
        self._events = events

    async def search(self, payer_email: str) -> InvoiceSearchResponse:
        """The Payer's Outstanding Invoices, as Catalog products."""
        reported = await self._invoice_api.invoices_of(payer_email)
        # A settled Invoice is not something an Agent can pay, so it is not in the
        # catalogue at all — unlike a shop's out-of-stock item, which may return.
        outstanding = [record for record in reported if record["outstanding"]]

        await self._events.publish(
            "ucp.catalog_searched",
            payload={
                "payer_email": payer_email,
                "invoices_returned": len(outstanding),
            },
        )

        return InvoiceSearchResponse(
            ucp=ResponseCatalogSchema(
                version=config.get_server_version(),
                capabilities={
                    CATALOG_SEARCH: [{"version": config.get_server_version()}],
                    INVOICE_EXTENSION: [
                        {
                            "version": config.get_server_version(),
                            "extends": CATALOG_SEARCH,
                        }
                    ],
                },
            ),
            products=[_as_product(record) for record in outstanding],
        )


def _as_product(reported: dict) -> InvoiceProduct:
    """Present one Invoice as a Catalog product.

    An Agent that never fetched the extension still sees something it can act on:
    a titled product priced at the Balance Due, carrying one variant — because
    paying an Invoice is not a choice between sizes, and the variant id is what
    Checkout will name as its line item.
    """
    invoice = as_invoice(reported)
    title = f"Invoice {invoice.doc_number}"
    description = Description(
        plain=f"{invoice.merchant.name} — {invoice.doc_number}, due {invoice.due_date}."
    )
    return InvoiceProduct(
        id=reported["id"],
        title=title,
        description=description,
        # The Balance Due, not the original total: a part-paid Invoice costs what
        # is left on it, and an Agent reading only the price must not overpay.
        price_range=PriceRange(min=invoice.balance_due, max=invoice.balance_due),
        list_price_range=PriceRange(
            min=invoice.original_total, max=invoice.original_total
        ),
        variants=[
            Variant(
                id=reported["id"],
                title=title,
                description=description,
                price=invoice.balance_due,
                list_price=invoice.original_total,
                availability=Availability(available=True, status="in_stock"),
            )
        ],
        **{INVOICE_EXTENSION: invoice},
    )
