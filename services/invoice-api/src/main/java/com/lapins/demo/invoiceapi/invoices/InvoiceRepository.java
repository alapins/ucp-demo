package com.lapins.demo.invoiceapi.invoices;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

interface InvoiceRepository extends JpaRepository<Invoice, String> {

  List<Invoice> findByPayerEmail(String email);
}
