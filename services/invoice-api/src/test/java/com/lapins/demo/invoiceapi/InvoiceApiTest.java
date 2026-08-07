package com.lapins.demo.invoiceapi;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/**
 * The Invoice API Server at its HTTP boundary — what a Merchant operator can create
 * and what the system of record then reports. Nothing here knows how any of it is
 * stored.
 *
 * <p>Tests find their own Invoice by Doc Number rather than assuming an empty list,
 * so they neither need nor perform a database reset between methods.
 */
@SpringBootTest(
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
    // The Merchant this server speaks for, stated by the test rather than inherited
    // from whatever the demo happens to be configured with.
    properties = {
      "demo.merchant.name=Ed's Surf Shop",
      "demo.merchant.contact-email=company@mailinator.com",
      "demo.merchant.payment-instructions=zo35gj8z4oe5fjpkxepg0m"
    })
class InvoiceApiTest {

  @Autowired private TestRestTemplate http;

  @Test
  void a_created_invoice_appears_in_the_invoice_list() {
    Map<String, Object> created =
        create(
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 3814,
                "dueDate", "2026-09-06"));

    Map<String, Object> listed = fromTheInvoiceList(created.get("docNumber"));

    assertThat(listed)
        .containsEntry("payerEmail", "vampserv@gmail.com")
        .containsEntry("balanceDueMinorUnits", 3814)
        .containsEntry("dueDate", "2026-09-06");
  }

  @Test
  void an_invoice_raised_without_a_due_date_falls_due_in_thirty_days() {
    Map<String, Object> created =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 20060));

    assertThat(created.get("dueDate")).isEqualTo(LocalDate.now().plusDays(30).toString());
  }

  @Test
  void the_invoice_list_can_be_narrowed_to_one_payer() {
    Map<String, Object> theirs =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 3814));
    Map<String, Object> someone_elses =
        create(Map.of("payerEmail", "quite.separate@example.com", "originalTotalMinorUnits", 3814));

    List<Map<String, Object>> narrowed =
        http.getForObject("/invoices?payerEmail=vampserv@gmail.com", List.class);

    assertThat(narrowed.stream().map(invoice -> invoice.get("docNumber")))
        .contains(theirs.get("docNumber"))
        .doesNotContain(someone_elses.get("docNumber"));
  }

  @Test
  void an_invoice_names_the_merchant_it_is_owed_to() {
    Map<String, Object> created =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 3814));

    assertThat(fromTheInvoiceList(created.get("docNumber")).get("merchant"))
        .isEqualTo(
            Map.of(
                "name", "Ed's Surf Shop",
                "contactEmail", "company@mailinator.com",
                "paymentInstructions", "zo35gj8z4oe5fjpkxepg0m"));
  }

  @Test
  void a_newly_raised_invoice_owes_the_whole_of_its_original_total() {
    // Balance Due and the original total are separate figures that happen to agree
    // here, because nothing has been paid. They part company once payment lands.
    Map<String, Object> created =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 66874));

    assertThat(fromTheInvoiceList(created.get("docNumber")))
        .containsEntry("originalTotalMinorUnits", 66874)
        .containsEntry("balanceDueMinorUnits", 66874);
  }

  @Test
  void an_invoice_is_denominated_in_the_merchants_currency_unless_told_otherwise() {
    Map<String, Object> assumed =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 3814));
    Map<String, Object> stated =
        create(
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 3814,
                "currency", "EUR"));

    assertThat(fromTheInvoiceList(assumed.get("docNumber"))).containsEntry("currency", "USD");
    assertThat(fromTheInvoiceList(stated.get("docNumber"))).containsEntry("currency", "EUR");
  }

  @Test
  void an_invoice_states_which_payment_methods_it_will_accept() {
    Map<String, Object> cardOnly =
        create(
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 100000,
                "allowedPaymentMethods", List.of("CARD")));

    assertThat(fromTheInvoiceList(cardOnly.get("docNumber")))
        .containsEntry("allowedPaymentMethods", List.of("CARD"));
  }

  @Test
  void an_invoice_raised_without_stated_payment_methods_takes_bank_or_card() {
    Map<String, Object> created =
        create(Map.of("payerEmail", "vampserv@gmail.com", "originalTotalMinorUnits", 3814));

    assertThat(fromTheInvoiceList(created.get("docNumber")))
        .containsEntry("allowedPaymentMethods", List.of("BANK", "CARD"));
  }

  @Test
  void an_invoice_whose_due_date_has_passed_is_overdue() {
    Map<String, Object> created =
        create(
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 43000,
                "dueDate", "2019-03-28"));

    // Overdue is a kind of Outstanding, not an alternative to it: the money is still
    // owed, it is merely also late.
    assertThat(fromTheInvoiceList(created.get("docNumber")))
        .containsEntry("outstanding", true)
        .containsEntry("overdue", true);
  }

  @Test
  void an_invoice_still_within_its_term_is_outstanding_without_being_overdue() {
    Map<String, Object> created =
        create(
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 43000,
                "dueDate", LocalDate.now().plusDays(7).toString()));

    assertThat(fromTheInvoiceList(created.get("docNumber")))
        .containsEntry("outstanding", true)
        .containsEntry("overdue", false);
  }

  @Test
  void doc_numbers_are_opaque_rather_than_a_counter() {
    List<String> minted =
        IntStream.range(0, 10)
            .mapToObj(
                each ->
                    (String)
                        create(
                                Map.of(
                                    "payerEmail", "vampserv@gmail.com",
                                    "originalTotalMinorUnits", 1000,
                                    "dueDate", "2026-09-06"))
                            .get("docNumber"))
            .toList();

    assertThat(minted).doesNotHaveDuplicates();
    // A Doc Number may legitimately look like a number — the reference product prints
    // 1022 alongside kIV88PDO. What it may never be is a counter, because then anyone
    // holding one Invoice could address the Merchant's next one.
    for (int earlier = 0; earlier < minted.size() - 1; earlier++) {
      assertThat(areConsecutiveIntegers(minted.get(earlier), minted.get(earlier + 1)))
          .as("%s then %s", minted.get(earlier), minted.get(earlier + 1))
          .isFalse();
    }
  }

  private static boolean areConsecutiveIntegers(String earlier, String later) {
    try {
      return Long.parseLong(later) - Long.parseLong(earlier) == 1;
    } catch (NumberFormatException notEvenNumeric) {
      return false;
    }
  }

  private Map<String, Object> create(Map<String, Object> request) {
    ResponseEntity<Map> response = http.postForEntity("/invoices", request, Map.class);
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    return response.getBody();
  }

  private Map<String, Object> fromTheInvoiceList(Object docNumber) {
    List<Map<String, Object>> invoices = http.getForObject("/invoices", List.class);
    return invoices.stream()
        .filter(invoice -> docNumber.equals(invoice.get("docNumber")))
        .findFirst()
        .orElseThrow(() -> new AssertionError("no Invoice " + docNumber + " in " + invoices));
  }
}
