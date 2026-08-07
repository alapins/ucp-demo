import { money, state, type Invoice } from "./invoices";

/** What the Merchant operator checks the Agent's work against. */
export function InvoiceList({ invoices }: { invoices: Invoice[] }) {
  if (invoices.length === 0) {
    return <p className="quiet">No Invoices raised yet.</p>;
  }
  return (
    <table className="invoices" data-testid="invoice-list">
      <thead>
        <tr>
          <th>Doc Number</th>
          <th>Payer</th>
          <th>Due date</th>
          <th>Balance Due</th>
          <th>State</th>
          <th>Payable by</th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((invoice) => (
          <tr key={invoice.id} data-doc-number={invoice.docNumber}>
            <td className="doc-number">{invoice.docNumber}</td>
            <td className="quiet">{invoice.payerEmail}</td>
            <td>{invoice.dueDate}</td>
            <td className="amount">
              {money(invoice.balanceDueMinorUnits, invoice.currency)}
            </td>
            <td className={`state ${state(invoice).toLowerCase()}`}>
              {state(invoice)}
            </td>
            <td className="quiet">
              {invoice.allowedPaymentMethods
                .map((method) => method.toLowerCase())
                .join(" or ")}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
