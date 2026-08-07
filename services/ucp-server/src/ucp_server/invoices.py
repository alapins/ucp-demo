"""Invoices, as the Invoice Extension exposes them.

The mapping in this module is the whole of the exposure layer's judgement: it
takes what the Invoice API said and says it again in UCP's vocabulary. It reads
nothing else, decides nothing, and keeps nothing — every field below traces to a
field of the record it was handed.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from ucp_sdk.models.schemas.shopping.types.price import Price

EXTENSION = "com.lapins.demo.invoicing.invoice"


class Merchant(BaseModel):
    """The business owed the Balance Due."""

    model_config = ConfigDict(extra="forbid")

    name: str
    contact_email: EmailStr | None = None
    payment_instructions: str | None = None


class Payer(BaseModel):
    """The party that owes the Balance Due.

    Identified by email rather than by an account: in the reference product the
    Payer arrives on an unauthenticated link and holds no account at all.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class Invoice(BaseModel):
    """Invoice facts, exactly as the system of record reports them.

    `extra="forbid"` is the "exposes only Invoice fields" rule made mechanical:
    a field that creeps into the Invoice API's response cannot leak through this
    extension without someone naming it here first.
    """

    model_config = ConfigDict(extra="forbid")

    doc_number: str
    due_date: str
    balance_due: Price
    original_total: Price
    outstanding: bool
    overdue: bool
    allowed_payment_methods: list[str] = Field(default_factory=list)
    merchant: Merchant
    payer: Payer


def as_invoice(reported: dict) -> Invoice:
    """Read one Invoice out of the Invoice API's report of it."""
    currency = reported["currency"]
    merchant = reported["merchant"]
    return Invoice(
        doc_number=reported["docNumber"],
        due_date=reported["dueDate"],
        # Currency travels inside the money it belongs to, as everywhere else in
        # UCP, so an amount and its currency cannot come apart downstream.
        balance_due=Price(amount=reported["balanceDueMinorUnits"], currency=currency),
        original_total=Price(
            amount=reported["originalTotalMinorUnits"], currency=currency
        ),
        outstanding=reported["outstanding"],
        overdue=reported["overdue"],
        allowed_payment_methods=reported["allowedPaymentMethods"],
        merchant=Merchant(
            name=merchant["name"],
            contact_email=merchant["contactEmail"],
            payment_instructions=merchant["paymentInstructions"],
        ),
        payer=Payer(email=reported["payerEmail"]),
    )
