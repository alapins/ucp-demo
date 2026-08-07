package com.lapins.demo.invoiceapi.invoices;

import java.time.LocalDate;
import java.util.List;
import java.util.Set;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** What a Merchant operator can do to Invoices, over HTTP. */
@RestController
@RequestMapping("/invoices")
class InvoiceController {

  private final Invoicing invoicing;

  InvoiceController(Invoicing invoicing) {
    this.invoicing = invoicing;
  }

  /** Due Date and Allowed Payment Methods may be left out; the Invoice supplies both. */
  record CreateInvoice(
      String payerEmail,
      long originalTotalMinorUnits,
      String currency,
      LocalDate dueDate,
      Set<PaymentMethod> allowedPaymentMethods) {}

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  InvoiceView create(@RequestBody CreateInvoice request) {
    Invoice issued =
        invoicing.issue(
            request.payerEmail(),
            request.originalTotalMinorUnits(),
            request.currency(),
            request.dueDate(),
            request.allowedPaymentMethods());
    return InvoiceView.of(issued, LocalDate.now());
  }

  /** How much of the Balance Due to settle. */
  record PayInvoice(long amountMinorUnits) {}

  /**
   * Pays an Invoice, in whole or in part.
   *
   * <p>Modelled as creating a payment against the Invoice rather than as setting it paid,
   * because the Merchant records payments and derives Outstanding from them — and because
   * an Invoice may one day take more than one.
   */
  @PostMapping("/{invoiceId}/payments")
  @ResponseStatus(HttpStatus.CREATED)
  InvoiceView pay(@PathVariable String invoiceId, @RequestBody PayInvoice request) {
    Invoice paid = invoicing.pay(invoiceId, request.amountMinorUnits());
    return InvoiceView.of(paid, LocalDate.now());
  }

  /** Every Invoice, or only one Payer's — which is what the UCP layer will ask for. */
  @GetMapping
  List<InvoiceView> list(@RequestParam(required = false) String payerEmail) {
    List<Invoice> found =
        payerEmail == null ? invoicing.all() : invoicing.forPayer(payerEmail);
    // Read once, so every Invoice in one list is judged Overdue against the same day.
    LocalDate today = LocalDate.now();
    return found.stream().map(invoice -> InvoiceView.of(invoice, today)).toList();
  }
}
