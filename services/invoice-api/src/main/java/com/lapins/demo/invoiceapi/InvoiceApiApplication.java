package com.lapins.demo.invoiceapi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * The Invoice API Server.
 *
 * <p>A walking skeleton: it holds a place in the topology and proves it can reach the
 * Event Bus. Invoices, the payment simulator, and persistence arrive in later tickets.
 */
@SpringBootApplication
public class InvoiceApiApplication {

  public static void main(String[] args) {
    SpringApplication.run(InvoiceApiApplication.class, args);
  }
}
