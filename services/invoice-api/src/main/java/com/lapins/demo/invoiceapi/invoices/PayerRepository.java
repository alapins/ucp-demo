package com.lapins.demo.invoiceapi.invoices;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

interface PayerRepository extends JpaRepository<Payer, String> {

  Optional<Payer> findByEmail(String email);
}
