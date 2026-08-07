import { useEffect, useState } from "react";

export type DemoEvent = {
  id: string;
  occurred_at: string;
  type: string;
  service: string;
  correlation_id: string;
  payload: Record<string, unknown>;
};

export type Connection = "connecting" | "live" | "reconnecting";

const eventBusUrl =
  import.meta.env.VITE_EVENT_BUS_URL ?? "http://localhost:8100";

export type Window = "merchant" | "agent";

/**
 * Holds this window's live subscription to the Event Bus.
 *
 * The window names itself, and the bus sends only what that window is entitled to
 * see — the other side's events never reach this connection. See WINDOWS in the
 * Event Bus for why that is a boundary rather than a filter.
 *
 * Reconnection is EventSource's own: on a drop it waits for the interval the bus
 * advertised and comes back quoting the last event id it saw, so the bus resumes
 * rather than repeating the log.
 */
export function useEventStream(window: Window) {
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [connection, setConnection] = useState<Connection>("connecting");

  useEffect(() => {
    const stream = new EventSource(`${eventBusUrl}/events?window=${window}`);

    stream.onopen = () => setConnection("live");
    stream.onerror = () => setConnection("reconnecting");
    stream.onmessage = (frame) => {
      const event = JSON.parse(frame.data) as DemoEvent;
      setEvents((seen) =>
        seen.some((each) => each.id === event.id) ? seen : [...seen, event],
      );
    };

    return () => stream.close();
  }, [window]);

  return { events, connection };
}
