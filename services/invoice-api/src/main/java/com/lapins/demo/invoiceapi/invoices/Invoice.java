package com.lapins.demo.invoiceapi.invoices;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import java.time.LocalDate;
import java.util.EnumSet;
import java.util.Locale;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** A request for payment issued by the Merchant to a Payer. */
@Entity
public class Invoice {

  @Id private String id;

  /**
   * The identifier a human reads off the Invoice. Deliberately opaque: the reference
   * product's Doc Numbers are things like {@code kIV88PDO}, not a counter.
   */
  @Column(unique = true, nullable = false)
  private String docNumber;

  @ManyToOne(optional = false)
  @JoinColumn(name = "merchant_id", nullable = false)
  private Merchant merchant;

  @ManyToOne(optional = false)
  @JoinColumn(name = "payer_id", nullable = false)
  private Payer payer;

  /** What the Invoice was raised for. Never changes once issued. */
  @Column(nullable = false)
  private long originalTotalMinorUnits;

  /** What is still owed. Falls below the original total once anything is paid. */
  @Column(nullable = false)
  private long balanceDueMinorUnits;

  /** ISO 4217. Both figures above are minor units of this. */
  @Column(nullable = false)
  private String currency;

  @Column(nullable = false)
  private LocalDate dueDate;

  // Eager because an Invoice is never useful without knowing what it will take, and
  // the representation is built after the entity has left its transaction.
  @ElementCollection(fetch = FetchType.EAGER)
  @CollectionTable(
      name = "invoice_allowed_payment_method",
      joinColumns = @JoinColumn(name = "invoice_id"))
  @Enumerated(EnumType.STRING)
  @Column(name = "payment_method", nullable = false)
  private Set<PaymentMethod> allowedPaymentMethods = EnumSet.noneOf(PaymentMethod.class);

  /**
   * How long an Invoice has to run when nobody says otherwise. The rule lives here, in
   * the system of record, rather than in the form that happens to pre-fill it — an
   * Invoice raised by seeding or by any later caller falls due on the same terms.
   */
  static final int DEFAULT_TERM_IN_DAYS = 30;

  /** What an Invoice takes when the Merchant does not narrow it. */
  static final Set<PaymentMethod> DEFAULT_PAYMENT_METHODS =
      EnumSet.of(PaymentMethod.BANK, PaymentMethod.CARD);

  /** What the Merchant bills in when nobody says otherwise. */
  static final String DEFAULT_CURRENCY = "USD";

  protected Invoice() {}

  public static Invoice issue(
      Merchant merchant,
      Payer payer,
      long originalTotalMinorUnits,
      String currency,
      LocalDate dueDate,
      Set<PaymentMethod> allowedPaymentMethods) {
    Invoice invoice = new Invoice();
    invoice.id = "inv-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
    invoice.docNumber = DocNumbers.mint();
    invoice.merchant = merchant;
    invoice.payer = payer;
    invoice.originalTotalMinorUnits = originalTotalMinorUnits;
    // Nothing has been paid yet, so the whole total is owed.
    invoice.balanceDueMinorUnits = originalTotalMinorUnits;
    invoice.currency =
        currency == null || currency.isBlank()
            ? DEFAULT_CURRENCY
            : currency.toUpperCase(Locale.ROOT);
    invoice.dueDate =
        dueDate != null ? dueDate : LocalDate.now().plusDays(DEFAULT_TERM_IN_DAYS);
    invoice.allowedPaymentMethods =
        allowedPaymentMethods == null || allowedPaymentMethods.isEmpty()
            ? EnumSet.copyOf(DEFAULT_PAYMENT_METHODS)
            : EnumSet.copyOf(allowedPaymentMethods);
    return invoice;
  }

  public String id() {
    return id;
  }

  public String docNumber() {
    return docNumber;
  }

  public Merchant merchant() {
    return merchant;
  }

  public Payer payer() {
    return payer;
  }

  public long originalTotalMinorUnits() {
    return originalTotalMinorUnits;
  }

  public long balanceDueMinorUnits() {
    return balanceDueMinorUnits;
  }

  public String currency() {
    return currency;
  }

  public LocalDate dueDate() {
    return dueDate;
  }

  /** In declaration order, so a caller comparing two Invoices sees a stable list. */
  public List<PaymentMethod> allowedPaymentMethods() {
    return allowedPaymentMethods.stream().sorted().toList();
  }

  /** Money is still owed on this Invoice. */
  public boolean isOutstanding() {
    return balanceDueMinorUnits > 0;
  }

  /**
   * Owed and late. Derived rather than stored: an Outstanding Invoice becomes Overdue
   * because a day passed, and nothing writes to it when that happens.
   */
  public boolean isOverdue(LocalDate today) {
    return isOutstanding() && dueDate.isBefore(today);
  }
}
