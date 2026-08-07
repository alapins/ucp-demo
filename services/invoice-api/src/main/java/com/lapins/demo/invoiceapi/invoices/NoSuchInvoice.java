package com.lapins.demo.invoiceapi.invoices;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/** No Invoice is held under the id a caller named. */
@ResponseStatus(HttpStatus.NOT_FOUND)
class NoSuchInvoice extends RuntimeException {

  NoSuchInvoice(String invoiceId) {
    super("no Invoice with id " + invoiceId);
  }
}
