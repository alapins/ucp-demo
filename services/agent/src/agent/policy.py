"""The Policy Engine — for now, a placeholder that allows everything.

This is a deliberate stub, not an oversight, and it is a whole module rather than a
line inside the run so that what replaces it has an obvious place to go. The demo it
serves shows the *cycle*: an Invoice is raised, the Agent finds it, decides about it,
and pays it. Deciding well is the next ticket.

What is already true, and must stay true, is the shape: a Decision is reached by code
that reads Invoice facts and returns a verdict with a machine-readable Reason Code. The
Agent's language model does not appear in this module and must not — per ADR 0003 it is
structurally incapable of authorizing payment, and that property is worth more than the
rules this file is currently missing.
"""

import dataclasses

ALLOW = "ALLOW"
DENY = "DENY"
REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

# The Reason Code standing in for real evaluation. Named for what it actually means, so
# that it reads as a stub on screen rather than as a rule that happened to pass.
NO_POLICY_IN_FORCE = "NO_POLICY_IN_FORCE"


@dataclasses.dataclass(frozen=True)
class Decision:
    """The Policy Engine's verdict on one Invoice."""

    invoice_id: str
    doc_number: str
    verdict: str
    reason_codes: tuple[str, ...]

    @property
    def is_allowed(self) -> bool:
        return self.verdict == ALLOW


def decide(invoice_id: str, invoice: dict) -> Decision:
    """Reach a Decision about one Invoice.

    Allows everything. The Payer has authored no Policy, so there is nothing for the
    Agent to refuse against — which is exactly the state a real Payer would be in before
    writing their first rule, and exactly why this cannot ship as the final behaviour.
    """
    return Decision(
        invoice_id=invoice_id,
        doc_number=invoice.get("doc_number", invoice_id),
        verdict=ALLOW,
        reason_codes=(NO_POLICY_IN_FORCE,),
    )
