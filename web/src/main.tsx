import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Link, Navigate, Route, BrowserRouter, Routes } from "react-router-dom";

import { EventLog } from "./EventLog";
import { MerchantWindow } from "./MerchantWindow";
import { RunAgentNow } from "./RunAgentNow";
import { useEventStream } from "./eventStream";
import { Window } from "./Window";
import "./styles.css";

/** What the Payer watches: their own Agent's activity, on their own machine. */
function AgentWindow() {
  const { events, connection } = useEventStream("agent");
  return (
    <Window title="Agent" connection={connection}>
      <section>
        <h2>Wake the Agent</h2>
        <RunAgentNow />
      </section>

      <section>
        <h2>Activity</h2>
        <EventLog events={events} />
      </section>
    </Window>
  );
}

function Landing() {
  return (
    <main className="window">
      <header>
        <h1>Invoice Payment Demo</h1>
      </header>
      <p className="quiet">Open each window in its own browser window.</p>
      <ul>
        <li>
          <Link to="/merchant">Merchant window</Link>
        </li>
        <li>
          <Link to="/agent">Agent window</Link>
        </li>
      </ul>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/merchant" element={<MerchantWindow />} />
        <Route path="/agent" element={<AgentWindow />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
