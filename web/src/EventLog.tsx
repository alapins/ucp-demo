import type { DemoEvent } from "./eventStream";

const time = (at: string) =>
  new Date(at).toLocaleTimeString(undefined, { hour12: false });

export function EventLog({ events }: { events: DemoEvent[] }) {
  if (events.length === 0) {
    return <p className="quiet">Waiting for the first event…</p>;
  }
  return (
    <ol className="events" data-testid="event-log">
      {events.map((event) => (
        <li key={event.id}>
          <span className="at">{time(event.occurred_at)}</span>
          <span className={`service ${event.service}`}>{event.service}</span>
          <span className="type">{event.type}</span>
          <span className="correlation">{event.correlation_id}</span>
        </li>
      ))}
    </ol>
  );
}
