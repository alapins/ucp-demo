# Policy constrains the Agent; humans outrank policy

Two rules that look like bugs, recorded so nobody "fixes" them.

**The LLM has no capabilities beyond five skills.** The Agent invokes `claude -p` with
`--tools ""` and `--strict-mcp-config`, so the model has no filesystem, no shell, and
nothing callable except the five skill tools served over MCP. The requirement that "the
LLM cannot directly authorize payment" is therefore structural rather than
instructional — there is no tool that would let it, so no prompt can talk it into one.
A future reader wondering why the agent container's model can't read its own config
files should read that as deliberate.

**A human may approve any DENY, including a hard limit breach.** An invoice denied by
`EXCEEDS_PER_INVOICE_LIMIT` is one click from being paid. This is the intended authority
model: Policy is a constraint on autonomous action, not on the Payer. The resulting
Mandate is a Human-Present Mandate and records the Reason Code it overrode, so the
override is auditable rather than silent.

## Consequences

Mandates come in two kinds and are not interchangeable — an Autonomous Mandate carries
only the Policy's authority, a Human-Present Mandate carries an Approval. Verification
must distinguish them; collapsing them into one code path would discard the distinction
AP2 exists to express.
