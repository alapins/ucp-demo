import { useEffect } from "react";

import { EventLog } from "./EventLog";
import { InvoiceList } from "./InvoiceList";
import { RaiseInvoice } from "./RaiseInvoice";
import { useEventStream } from "./eventStream";
import { useInvoices } from "./invoices";
import { Window } from "./Window";

/** What the Merchant operator watches: Invoice API and UCP Server activity. */
export function MerchantWindow() {
  const { events, connection } = useEventStream("merchant");
  const { invoices, error, reload } = useInvoices();

  // The list follows the stream, not the form. An Invoice raised in another window,
  // or a Balance Due the Agent has just cleared, reaches this list by the same route
  // as the operator's own — so what is on screen is the system of record's answer.
  const announcements = events.filter((event) =>
    event.type.startsWith("invoice."),
  ).length;
  useEffect(() => {
    void reload();
  }, [announcements, reload]);

  return (
    <Window title="Merchant" connection={connection}>
      <section>
        <h2>Raise an Invoice</h2>
        <RaiseInvoice />
      </section>

      <section>
        <h2>Invoices</h2>
        {error ? <p className="refused">{error}</p> : <InvoiceList invoices={invoices} />}
      </section>

      <section>
        <h2>Activity</h2>
        <EventLog events={events} />
      </section>
    </Window>
  );
}
