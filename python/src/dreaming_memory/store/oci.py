"""OCI Free Tier database connection helpers.

Two supported free-tier topologies (Postgres stays the SSOT):

1. **Postgres on Ampere A1** (recommended for dev) — a Postgres container runs
   on an Always-Free A1 VM; connect over the Tailscale mesh IP.
   DSN: postgresql://user:pass@<tailscale-ip>:5432/agent_memory

2. **OCI Database with PostgreSQL / Autonomous DB** — managed; connect via the
   provided connection string. For Autonomous DB (Oracle) use a separate
   adapter; this project targets Postgres-compatible endpoints.

This helper just builds/validates a DSN from fleet config or OCI metadata.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from dreaming_memory.config import FleetConfig, get_secret

# Fleet hosts (Tailscale IPs) — A1 nodes that can host Postgres.
FLEET_POSTGRES_HOSTS = {
    "bc-monitor": "100.78.210.57",
    "bc-scan-arm": "100.68.121.19",
    "bc-scan-2": "100.65.83.86",
}


def build_dsn(
    host: str = "bc-monitor",
    *,
    user: str = "postgres",
    password: str | None = None,
    dbname: str = "agent_memory",
    port: int = 5432,
) -> str:
    """Build a Postgres DSN for a named fleet host or raw hostname/IP."""
    password = quote_plus(password or get_secret("AGENT_MEMORY_DB_PASSWORD", "postgres") or "")
    resolved = FLEET_POSTGRES_HOSTS.get(host, host)
    return f"postgresql://{user}:{password}@{resolved}:{port}/{dbname}"


def resolve_database_url(prefer_fleet_host: str | None = None) -> str:
    """Return the effective DSN: explicit config wins, else fleet host DSN."""
    config = FleetConfig.load()
    if config.database_url:
        return config.database_url
    if prefer_fleet_host:
        return build_dsn(prefer_fleet_host)
    return build_dsn()
