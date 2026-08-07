package com.lapins.demo.invoiceapi.invoices;

import org.springframework.stereotype.Component;

/**
 * Payers, looked up by the only thing that identifies them.
 *
 * <p>A Payer is not enrolled before being invoiced: the Merchant raises an Invoice
 * against an email address, and that address becoming known to this server is all
 * there is to a Payer existing.
 */
@Component
class Payers {

  private final PayerRepository payers;

  Payers(PayerRepository payers) {
    this.payers = payers;
  }

  Payer identifiedBy(String email) {
    return payers.findByEmail(email).orElseGet(() -> payers.save(new Payer(email)));
  }
}
