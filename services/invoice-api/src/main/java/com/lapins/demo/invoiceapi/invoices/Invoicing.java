package com.lapins.demo.invoiceapi.invoices;

import com.lapins.demo.invoiceapi.events.EventPublisher;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;

/** Raising Invoices and reading them back — the whole of what this server is for. */
@Service
class Invoicing {

  private final InvoiceRepository invoices;
  private final Merchants merchants;
  private final Payers payers;
  private final EventPublisher events;

  Invoicing(
      InvoiceRepository invoices, Merchants merchants, Payers payers, EventPublisher events) {
    this.invoices = invoices;
    this.merchants = merchants;
    this.payers = payers;
    this.events = events;
  }

  Invoice issue(
      String payerEmail,
      long originalTotalMinorUnits,
      String currency,
      LocalDate dueDate,
      Set<PaymentMethod> allowedPaymentMethods) {
    Invoice issued =
        invoices.save(
            Invoice.issue(
                merchants.theMerchant(),
                payers.identifiedBy(payerEmail),
                originalTotalMinorUnits,
                currency,
                dueDate,
                allowedPaymentMethods));
    announce(issued);
    return issued;
  }

  List<Invoice> all() {
    return invoices.findAll();
  }

  List<Invoice> forPayer(String payerEmail) {
    return invoices.findByPayerEmail(payerEmail);
  }

  /**
   * Tells the demo an Invoice exists.
   *
   * <p>The Invoice's own id is the correlation identifier, so the Decision, Checkout,
   * Mandate and payment that follow all thread onto it and any service can rejoin the
   * story holding nothing but the Invoice.
   */
  private void announce(Invoice issued) {
    events.publish(
        "invoice.created",
        issued.id(),
        Map.of(
            "invoice_id", issued.id(),
            "doc_number", issued.docNumber(),
            "payer_email", issued.payer().email(),
            "balance_due_minor_units", issued.balanceDueMinorUnits(),
            "currency", issued.currency(),
            "due_date", issued.dueDate().toString()));
  }
}
