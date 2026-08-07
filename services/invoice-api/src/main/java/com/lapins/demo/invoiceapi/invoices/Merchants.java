package com.lapins.demo.invoiceapi.invoices;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * The one Merchant this server speaks for.
 *
 * <p>Its details come from configuration and are written into the database on startup,
 * so the Merchant is a persisted record like any other rather than a value read out of
 * the environment at each request. Multi-Merchant support is out of scope.
 */
@Component
class Merchants {

  private final MerchantRepository merchants;
  private final String name;
  private final String contactEmail;
  private final String paymentInstructions;

  Merchants(
      MerchantRepository merchants,
      @Value("${demo.merchant.name}") String name,
      @Value("${demo.merchant.contact-email}") String contactEmail,
      @Value("${demo.merchant.payment-instructions}") String paymentInstructions) {
    this.merchants = merchants;
    this.name = name;
    this.contactEmail = contactEmail;
    this.paymentInstructions = paymentInstructions;
  }

  @PostConstruct
  void record() {
    merchants.save(new Merchant(name, contactEmail, paymentInstructions));
  }

  Merchant theMerchant() {
    return merchants
        .findById(Merchant.THE_MERCHANT)
        .orElseThrow(() -> new IllegalStateException("the Merchant was never recorded"));
  }
}
