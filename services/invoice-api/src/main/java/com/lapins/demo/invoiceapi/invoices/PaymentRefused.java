package com.lapins.demo.invoiceapi.invoices;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * A payment the system of record will not apply.
 *
 * <p>A 422 rather than a 400: the request was well-formed and the caller is entitled to
 * make it, but the Invoice is not in a state that admits it. An Agent that reads the
 * difference knows to re-read authoritative state rather than to retry the same payment.
 */
@ResponseStatus(HttpStatus.UNPROCESSABLE_ENTITY)
class PaymentRefused extends RuntimeException {

  PaymentRefused(String message) {
    super(message);
  }
}
