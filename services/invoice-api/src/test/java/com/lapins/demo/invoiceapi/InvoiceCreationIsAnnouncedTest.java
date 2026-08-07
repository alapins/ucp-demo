package com.lapins.demo.invoiceapi;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

/**
 * What the Merchant's side of the demo hears when an Invoice is raised.
 *
 * <p>This is the event the merchant window draws, and the Wake that later wakes the
 * Agent, so its shape is a contract rather than a log line.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InvoiceCreationIsAnnouncedTest {

  // Started when this class loads, so the address is known before Spring reads it.
  private static final StubEventBus BUS = StubEventBus.start();

  @DynamicPropertySource
  static void publishToTheStubBus(DynamicPropertyRegistry properties) {
    properties.add("demo.event-bus-url", BUS::url);
  }

  @Autowired private TestRestTemplate http;

  @Test
  void creating_an_invoice_announces_it_to_the_merchants_side_of_the_demo() {
    Map<String, Object> created =
        http.postForObject(
            "/invoices",
            Map.of(
                "payerEmail", "vampserv@gmail.com",
                "originalTotalMinorUnits", 20060,
                "dueDate", "2019-03-28"),
            Map.class);

    Map<String, Object> announced = BUS.announcementOf("invoice.created");

    assertThat(announced)
        .containsEntry("service", "invoice-api")
        // Everything that later happens to this Invoice — the Agent's Decision, the
        // Checkout, the Mandate, the payment — threads on the Invoice's own id, so any
        // service can rejoin the story holding nothing but the Invoice.
        .containsEntry("correlation_id", created.get("id"));
    assertThat(announced.get("payload"))
        .isEqualTo(
            Map.of(
                "invoice_id", created.get("id"),
                "doc_number", created.get("docNumber"),
                "payer_email", "vampserv@gmail.com",
                "balance_due_minor_units", 20060,
                // A figure without its currency is not a figure anyone can act on.
                "currency", "USD",
                "due_date", "2019-03-28"));
  }
}
