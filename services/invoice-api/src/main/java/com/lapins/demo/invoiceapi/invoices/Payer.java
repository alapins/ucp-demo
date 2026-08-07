package com.lapins.demo.invoiceapi.invoices;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import java.util.UUID;

/**
 * The party that owes the Balance Due.
 *
 * <p>Identified by email and nothing else. The Payer in the reference product arrives
 * on an unauthenticated link and holds no account, so there is no name, no password,
 * and nothing to sign in to.
 */
@Entity
public class Payer {

  @Id private String id;

  @Column(unique = true, nullable = false)
  private String email;

  protected Payer() {}

  Payer(String email) {
    this.id = "payer-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
    this.email = email;
  }

  public String id() {
    return id;
  }

  public String email() {
    return email;
  }
}
