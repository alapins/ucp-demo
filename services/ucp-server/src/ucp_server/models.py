#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Unified models for the UCP REST server.

These models extend the base UCP SDK models by combining multiple extensions
(e.g., Fulfillment, Discount, Buyer Consent) into unified checkout and order
objects used by the server implementation.

This Merchant's own extension, `com.lapins.demo.invoicing.invoice`, is composed
onto the Catalog the same way: as a mixin over an SDK model, so that the vendor
extension is built out of the protocol rather than around it.
"""

from typing import Any
from pydantic import ConfigDict, Field
from ucp_sdk.models.schemas.shopping.ap2_mandate import Checkout as Ap2Checkout
from ucp_sdk.models.schemas.shopping.catalog_search import SearchResponse
from ucp_sdk.models.schemas.shopping.types.product import Product

from ucp_server.invoices import EXTENSION, Invoice
from ucp_sdk.models.schemas.shopping.buyer_consent import (
  Checkout as BuyerConsentCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.discount import (
  Checkout as DiscountCheckoutResp,
  DiscountsObject,
)
from ucp_sdk.models.schemas.shopping.fulfillment import (
  Checkout as FulfillmentCheckout,
  Fulfillment,
)

from ucp_sdk.models.schemas.shopping.order import Order
from ucp_sdk.models.schemas.shopping.order import PlatformSchema

from ucp_sdk.models.schemas.shopping.checkout_create_request import (
  CheckoutCreateRequest,
)
from ucp_sdk.models.schemas.shopping.checkout_update_request import (
  CheckoutUpdateRequest,
)


class InvoiceProduct(Product):
  """Product model supporting the Invoice extension.

  The extension keys itself by its own reverse-domain name, which is not a legal
  Python identifier, so the field is aliased. Serialization is by alias — the
  wire is where the name has to be right.
  """

  model_config = ConfigDict(extra="allow", populate_by_name=True)

  invoice: Invoice | None = Field(None, alias=EXTENSION)


class InvoiceSearchResponse(SearchResponse):
  """Catalog Search response whose products are Invoices."""

  products: list[InvoiceProduct]


class UnifiedOrder(Order):
  """Order model supporting extensions."""


class UnifiedCheckout(
  BuyerConsentCheckoutResp,
  FulfillmentCheckout,
  DiscountCheckoutResp,
  Ap2Checkout,
):
  """Checkout model supporting various extensions."""

  platform: PlatformSchema | None = None


class UnifiedCheckoutCreateRequest(CheckoutCreateRequest):
  """Create request model combining base fields and extensions."""

  fulfillment: Fulfillment | None = None
  discounts: DiscountsObject | None = None
  buyer_consent: Any | None = None


class UnifiedCheckoutUpdateRequest(CheckoutUpdateRequest):
  """Update request model combining base fields and extensions."""

  fulfillment: Fulfillment | None = None
  discounts: DiscountsObject | None = None
  buyer_consent: Any | None = None


InvoiceProduct.model_rebuild()
InvoiceSearchResponse.model_rebuild()
UnifiedCheckout.model_rebuild()
UnifiedCheckoutCreateRequest.model_rebuild()
UnifiedCheckoutUpdateRequest.model_rebuild()
UnifiedOrder.model_rebuild()
