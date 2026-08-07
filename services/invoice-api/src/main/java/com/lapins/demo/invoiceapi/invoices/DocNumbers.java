package com.lapins.demo.invoiceapi.invoices;

import java.security.SecureRandom;

/** Mints the identifier a human reads off an Invoice. */
final class DocNumbers {

  // Mixed case and digits, matching the shape the reference product prints. A Doc
  // Number carries no meaning and admits no arithmetic: two Invoices raised one after
  // the other are not 1022 and 1023.
  private static final String ALPHABET =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  private static final int LENGTH = 8;
  private static final SecureRandom RANDOM = new SecureRandom();

  private DocNumbers() {}

  static String mint() {
    StringBuilder docNumber = new StringBuilder(LENGTH);
    for (int character = 0; character < LENGTH; character++) {
      docNumber.append(ALPHABET.charAt(RANDOM.nextInt(ALPHABET.length())));
    }
    return docNumber.toString();
  }
}
