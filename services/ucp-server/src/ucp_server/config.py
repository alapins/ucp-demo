#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Shared configuration for the UCP Server.

Forked from the UCP Python reference merchant server (see FORK.md). The reference
reads its settings from absl command-line flags, which suits a sample you launch
by hand; this demo is started by Docker Compose, so the same settings are read
from the environment instead. The attribute names are unchanged so that the
vendored code reading `config.FLAGS.x` needs no edit.
"""

import json
import os
import uuid
from pathlib import Path

# checkout.json annotates `currency` with `ucp_request: omit` and describes
# it as "reflecting the merchant's market determination ... buyers provide
# signals, merchants determine currency". A conformant platform therefore does
# not send it, and the generated CheckoutCreateRequest has no such field. This
# demo serves a single market, so the determination is a constant.
DEFAULT_CURRENCY = "USD"

_SERVER_VERSION_CACHE = None


def get_default_currency() -> str:
  """Return the currency this business trades in."""
  return DEFAULT_CURRENCY


def get_server_version() -> str:
  """Read and cache the server version from the discovery profile."""
  global _SERVER_VERSION_CACHE
  if _SERVER_VERSION_CACHE:
    return _SERVER_VERSION_CACHE

  current_dir = Path(__file__).resolve().parent
  profile_path = current_dir / "routes" / "discovery_profile.json"

  with profile_path.open() as f:
    data = json.load(f)
    _SERVER_VERSION_CACHE = data["ucp"]["version"]
    return _SERVER_VERSION_CACHE


def _flag(name: str, default: str) -> str:
  return os.environ.get(name, default)


def _boolean_flag(name: str, default: bool) -> bool:
  return _flag(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class _Settings:
  """The reference server's flags, read from the environment."""

  @property
  def require_signatures(self) -> bool:
    """Reject requests whose RFC 9421 signature is missing or invalid.

    When false (the default), signatures are still verified when present, but
    unsigned or invalid requests are allowed and only logged.
    """
    return _boolean_flag("UCP_REQUIRE_SIGNATURES", False)

  @property
  def allow_insecure_profile_urls(self) -> bool:
    """Permit http and loopback/private UCP-Agent profile URLs.

    For localhost demos and CI only; never enable in production, as it disables
    SSRF protections. The whole demo runs on one machine behind Compose service
    names, so it defaults to true here where the reference defaults to false.
    """
    return _boolean_flag("UCP_ALLOW_INSECURE_PROFILE_URLS", True)

  @property
  def simulation_secret(self) -> str:
    """Secret key for simulation endpoints."""
    return _flag("UCP_SIMULATION_SECRET", str(uuid.uuid4()))

  @property
  def transactions_db_path(self) -> str:
    """Where the Checkout state machine keeps its sessions.

    Checkouts are the UCP Server's own workings, not Invoice state — the Invoice
    API remains the sole system of record for anything an Invoice knows.
    """
    return _flag("UCP_TRANSACTIONS_DB_PATH", "/tmp/ucp-transactions.db")

  @property
  def products_db_path(self) -> str:
    """Unused: this Merchant's catalogue is Invoices, read live over HTTP.

    The reference server ships a product database because a flower shop owns its
    inventory. Here the Catalog delegates to the Invoice API on every search, so
    the path exists only to satisfy the vendored startup and holds nothing.
    """
    return _flag("UCP_PRODUCTS_DB_PATH", "/tmp/ucp-products.db")


FLAGS = _Settings()
