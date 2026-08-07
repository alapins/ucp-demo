package com.lapins.demo.invoiceapi.invoices;

/** How the Merchant appears to anything outside this server. */
record MerchantView(String name, String contactEmail, String paymentInstructions) {

  static MerchantView of(Merchant merchant) {
    return new MerchantView(
        merchant.name(), merchant.contactEmail(), merchant.paymentInstructions());
  }
}
