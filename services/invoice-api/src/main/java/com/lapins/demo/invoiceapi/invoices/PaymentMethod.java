package com.lapins.demo.invoiceapi.invoices;

/**
 * An instrument an Invoice will accept.
 *
 * <p>Not uniform across a Merchant's Invoices — the reference product groups them into
 * "payable by bank or card" and "payable by card only". Nothing in this demo reads this
 * to make a decision; it is here because the real product exposes it.
 */
public enum PaymentMethod {
  BANK,
  CARD
}
