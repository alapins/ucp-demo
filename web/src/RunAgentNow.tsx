import { useState } from "react";

import { wakeAgent, type RunReport } from "./agent";

/** Waking the Agent by hand — the Wake a human performs. */
export function RunAgentNow() {
  const [running, setRunning] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const [report, setReport] = useState<RunReport | null>(null);

  async function run() {
    setRunning(true);
    setRefused(null);
    try {
      // What the run did is told by the stream below, not by this button. The report is
      // kept only so that a run which found nothing is distinguishable from one that
      // never started — on screen those look identical.
      setReport(await wakeAgent("Run Agent Now"));
    } catch (refusal) {
      setRefused(String(refusal));
      setReport(null);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="raise">
      <button type="button" onClick={run} disabled={running}>
        {running ? "Running…" : "Run Agent Now"}
      </button>
      {report && (
        <p className="quiet">
          {report.gave_up
            ? `Gave up: ${report.gave_up}`
            : `Discovered ${report.discovered}, paid ${report.paid}.`}
        </p>
      )}
      {refused && <p className="refused">{refused}</p>}
    </div>
  );
}
