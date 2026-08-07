"""The Catalog Search endpoint, at the path the published REST binding names.

`POST /catalog/search` is not a path this demo chose; it is the one an Agent will
try after reading `services["dev.ucp.shopping"][transport=rest].endpoint` out of
the profile. Serving it there is the difference between a Merchant any conforming
agent can shop and one that needs prior arrangement.
"""

from fastapi import APIRouter, Body, Header
from ucp_sdk.models.schemas.shopping.catalog_search import SearchRequest

from ucp_server.models import InvoiceSearchResponse
from ucp_server.payers import Payers
from ucp_server.services.catalog_service import CatalogService


def catalog_router(catalog: CatalogService, payers: Payers) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/catalog/search",
        response_model=InvoiceSearchResponse,
        response_model_exclude_none=True,
        operation_id="search_catalog",
        summary="Search Catalog",
    )
    async def search_catalog(
        body: SearchRequest = Body(default_factory=SearchRequest),
        x_api_key: str = Header(None, alias="X-API-Key"),
    ) -> InvoiceSearchResponse:
        """Return the Invoices this Merchant holds against the calling Payer.

        The request body's `query` and `filters` are read and ignored: this
        catalogue is one Payer's Invoices, which is small, complete, and already
        exactly what was asked for.
        """
        del body  # Unused.
        return await catalog.search(payers.identified_by(x_api_key))

    return router
