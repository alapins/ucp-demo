import { useState } from "react";

import { raiseInvoice, thirtyDaysFromToday } from "./invoices";

/**
 * The Merchant operator's way to produce any scenario on demand.
 *
 * <p>Amounts are typed the way they are written on an Invoice and sent as minor units,
 * which is the only unit anything downstream — Policy included — deals in.
 */
export function RaiseInvoice() {
  const [payerEmail, setPayerEmail] = useState("vampserv@gmail.com");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState(thirtyDaysFromToday);
  const [refused, setRefused] = useState<string | null>(null);
  const [raising, setRaising] = useState(false);

  async function submit(submitted: React.FormEvent) {
    submitted.preventDefault();
    setRaising(true);
    try {
      await raiseInvoice({
        payerEmail,
        originalTotalMinorUnits: Math.round(Number(amount) * 100),
        dueDate,
      });
      setRefused(null);
      setAmount("");
      // The list is not touched here. It reloads when invoice.created arrives from
      // the Event Bus, so what the operator sees is the system reacting rather than
      // this browser congratulating itself.
    } catch (refusal) {
      setRefused(String(refusal));
    } finally {
      setRaising(false);
    }
  }

  return (
    <form className="raise" onSubmit={submit}>
      <label>
        Payer email
        <input
          type="email"
          required
          value={payerEmail}
          onChange={(typed) => setPayerEmail(typed.target.value)}
        />
      </label>
      <label>
        Amount
        <input
          type="number"
          required
          min="0.01"
          step="0.01"
          placeholder="430.00"
          value={amount}
          onChange={(typed) => setAmount(typed.target.value)}
        />
      </label>
      <label>
        Due date
        <input
          type="date"
          required
          value={dueDate}
          onChange={(typed) => setDueDate(typed.target.value)}
        />
      </label>
      <button type="submit" disabled={raising}>
        Raise Invoice
      </button>
      {refused && <p className="refused">{refused}</p>}
    </form>
  );
}
