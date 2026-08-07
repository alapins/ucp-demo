package com.lapins.demo.invoiceapi.invoices;

import org.springframework.data.jpa.repository.JpaRepository;

interface MerchantRepository extends JpaRepository<Merchant, String> {}
