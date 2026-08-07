"""Invoices as the Invoice API reports them.

Hand-written to the Java service's `InvoiceView` record, camel case and all. The
integration test in `test_catalog_over_the_real_stack.py` is what keeps this
honest: if the two drift, that test fails where these would not.
"""


def as_the_invoice_api_reports_it(
    id="4f1c9e2a-0000-4000-8000-000000000001",
    doc_number="kIV88PDO",
    payer_email="ada@example.com",
    original_total_minor_units=12500,
    balance_due_minor_units=12500,
    currency="USD",
    due_date="2026-08-14",
    outstanding=True,
    overdue=False,
    allowed_payment_methods=("BANK", "CARD"),
    merchant_name="Demo Merchant",
):
    return {
        "id": id,
        "docNumber": doc_number,
        "merchant": {
            "name": merchant_name,
            "contactEmail": "billing@demo-merchant.example",
            "paymentInstructions": "Please pay by the due date.",
        },
        "payerEmail": payer_email,
        "originalTotalMinorUnits": original_total_minor_units,
        "balanceDueMinorUnits": balance_due_minor_units,
        "currency": currency,
        "dueDate": due_date,
        "outstanding": outstanding,
        "overdue": overdue,
        "allowedPaymentMethods": list(allowed_payment_methods),
    }
