const agentUrl = import.meta.env.VITE_AGENT_URL ?? "http://localhost:8200";

/** What a run reports back to whoever started it. */
export type RunReport = {
  woke_because: string;
  discovered?: number;
  paid?: number;
  gave_up?: string;
};

/**
 * Wake the Agent.
 *
 * The Agent has no other way to begin, so this is not a convenience button: it is one
 * of the four Wakes, differing from an Invoice being created only in what it says here.
 */
export async function wakeAgent(because: string): Promise<RunReport> {
  const response = await fetch(`${agentUrl}/agent/wake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ because }),
  });
  if (!response.ok) {
    throw new Error(`the Agent refused to run: ${response.status}`);
  }
  return response.json();
}
