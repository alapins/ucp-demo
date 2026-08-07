package com.lapins.demo.invoiceapi.invoices;

import java.time.LocalDate;
import java.util.List;

/**
 * How an Invoice appears to anything outside this server.
 *
 * <p>Outstanding and Overdue travel as two flags rather than one state, because Overdue
 * is a kind of Outstanding: an Invoice that is late is still owed. A caller wanting a
 * single label reads Overdue first.
 */
record InvoiceView(
    String id,
    String docNumber,
    MerchantView merchant,
    String payerEmail,
    long originalTotalMinorUnits,
    long balanceDueMinorUnits,
    String currency,
    LocalDate dueDate,
    boolean outstanding,
    boolean overdue,
    List<PaymentMethod> allowedPaymentMethods) {

  static InvoiceView of(Invoice invoice, LocalDate today) {
    return new InvoiceView(
        invoice.id(),
        invoice.docNumber(),
        MerchantView.of(invoice.merchant()),
        invoice.payer().email(),
        invoice.originalTotalMinorUnits(),
        invoice.balanceDueMinorUnits(),
        invoice.currency(),
        invoice.dueDate(),
        invoice.isOutstanding(),
        invoice.isOverdue(today),
        invoice.allowedPaymentMethods());
  }
}
