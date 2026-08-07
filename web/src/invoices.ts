import { useCallback, useEffect, useState } from "react";

export type PaymentMethod = "BANK" | "CARD";

export type Merchant = {
  name: string;
  contactEmail: string;
  paymentInstructions: string;
};

export type Invoice = {
  id: string;
  docNumber: string;
  merchant: Merchant;
  payerEmail: string;
  originalTotalMinorUnits: number;
  balanceDueMinorUnits: number;
  currency: string;
  dueDate: string;
  outstanding: boolean;
  overdue: boolean;
  allowedPaymentMethods: PaymentMethod[];
};

const invoiceApiUrl =
  import.meta.env.VITE_INVOICE_API_URL ?? "http://localhost:8080";

/** What the Merchant operator fills in. The server supplies everything else. */
export type NewInvoice = {
  payerEmail: string;
  originalTotalMinorUnits: number;
  dueDate: string;
};

export async function raiseInvoice(invoice: NewInvoice): Promise<void> {
  const response = await fetch(`${invoiceApiUrl}/invoices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(invoice),
  });
  if (!response.ok) {
    throw new Error(`the Invoice API refused the Invoice: ${response.status}`);
  }
}

/**
 * The Merchant's Invoices as the system of record currently reports them.
 *
 * <p>Nothing is held locally beyond the last answer: an Invoice's state is the Invoice
 * API's to say, and the Agent will be changing it from outside this browser.
 */
export function useInvoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const response = await fetch(`${invoiceApiUrl}/invoices`);
      if (!response.ok) throw new Error(`status ${response.status}`);
      setInvoices(await response.json());
      setError(null);
    } catch (unreachable) {
      setError(String(unreachable));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { invoices, error, reload };
}

const inMinorUnits = (currency: string) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency });

export const money = (minorUnits: number, currency: string) =>
  inMinorUnits(currency).format(minorUnits / 100);

/** Overdue first: an Invoice that is late is still Outstanding, and worse. */
export const state = (invoice: Invoice) =>
  invoice.overdue ? "Overdue" : invoice.outstanding ? "Outstanding" : "Paid";

/** The Due Date a new Invoice gets unless the operator picks another. */
export function thirtyDaysFromToday(): string {
  const due = new Date();
  due.setDate(due.getDate() + 30);
  return due.toISOString().slice(0, 10);
}
