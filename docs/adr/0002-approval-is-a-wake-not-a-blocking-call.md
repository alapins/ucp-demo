# Approval is a Wake, never a blocking call

When the Policy Engine returns REQUIRE_APPROVAL, the obvious design is a
human-in-the-loop tool call that blocks until someone clicks — and that is the design we
rejected. The Agent's LLM runs inside a `claude -p` subprocess; a blocking tool call
would hold a model turn open on a human's attention span, so any hesitation during a
live demo becomes a hung agent on screen. Instead the Agent persists the Decision, ends
the run, and treats a later Approval as just another **Wake** — the same mechanism that
already handles invoice-created events, scheduler ticks, and Run Agent Now.

## Consequences

Decisions must be durable and outlive the run that produced them, so the Agent owns a
decision store rather than holding state in memory. Every Agent run must be written to
start from persisted state, not from a conversation carried over from a previous run.
The payoff is that one mechanism serves four trigger sources, and no human ever has a
model turn waiting on them.
