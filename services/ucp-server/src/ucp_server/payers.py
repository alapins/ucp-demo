"""Which Payer an Agent is acting for.

A static API key, and nothing more: `dev.ucp.common.identity_linking` and any
OAuth flow are deliberately out of scope. The key's whole job is to name a Payer,
because a Catalog search that did not know whose Invoices to return would either
have to take the Payer's identity from the caller — who could then read anyone's
Invoices — or return the Merchant's entire ledger.
"""

import os

from ucp_server.exceptions import UcpError


class UnknownApiKeyError(UcpError):
    """Raised when a request carries no API key, or one naming no Payer."""

    def __init__(self, message: str):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class Payers:
    """Resolves an API key to the Payer it stands for."""

    def __init__(self, api_keys: dict[str, str]):
        self._by_key = dict(api_keys)

    @classmethod
    def from_environment(cls) -> "Payers":
        """Read `UCP_API_KEYS`, formatted `key:payer@example.com,key2:other@…`."""
        configured = os.environ.get("UCP_API_KEYS", "")
        pairs = (entry.split(":", 1) for entry in configured.split(",") if entry)
        return cls({key.strip(): email.strip() for key, email in pairs})

    def identified_by(self, api_key: str | None) -> str:
        """The email of the Payer this key acts for."""
        payer_email = self._by_key.get(api_key or "")
        if payer_email is None:
            # Deliberately says nothing about which keys exist.
            raise UnknownApiKeyError("the API key does not identify a Payer")
        return payer_email
