package com.lapins.demo.invoiceapi.invoices;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/** The business the Balance Due is owed to. */
@Entity
public class Merchant {

  /**
   * There is one Merchant. Multi-Merchant is out of scope, so the row has a fixed
   * identity rather than a generated one — the demo restarts into the same Merchant.
   */
  static final String THE_MERCHANT = "merchant-1";

  @Id private String id;

  @Column(nullable = false)
  private String name;

  @Column(nullable = false)
  private String contactEmail;

  /** Free text, printed beside the Invoices in the reference product. */
  @Column(nullable = false)
  private String paymentInstructions;

  protected Merchant() {}

  Merchant(String name, String contactEmail, String paymentInstructions) {
    this.id = THE_MERCHANT;
    this.name = name;
    this.contactEmail = contactEmail;
    this.paymentInstructions = paymentInstructions;
  }

  public String name() {
    return name;
  }

  public String contactEmail() {
    return contactEmail;
  }

  public String paymentInstructions() {
    return paymentInstructions;
  }
}
