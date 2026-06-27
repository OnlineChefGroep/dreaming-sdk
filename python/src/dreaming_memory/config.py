"""Central config + secrets loader for the agent memory fleet.

Resolution order (first match wins):
1. Process environment (os.environ)
2. Fleet env file (~/.openclaude/.env — `export KEY="val"` lines, never committed)
3. Per-host fallback (~/.config/agent-memory/.env)

Only read at runtime; secrets are never written to the repo.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_EXPORT_RE = re.compile(r'^\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.*)\s*$')

_DEFAULT_SECRET_FILES = (
    Path(os.environ.get("FLEET_ENV_FILE", "")) if os.environ.get("FLEET_ENV_FILE") else None,
    Path.home() / ".openclaude" / ".env",
    Path.home() / ".config" / "agent-memory" / ".env",
)


def _parse_env_file(path: Path | None) -> dict[str, str]:
    if not path or not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _EXPORT_RE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        out[key] = val.strip().strip('"').strip("'")
    return out


def load_fleet_secrets(extra_files: tuple[Path, ...] = ()) -> dict[str, str]:
    """Load fleet env files into os.environ without overwriting existing vars."""
    merged: dict[str, str] = {}
    for path in (*_DEFAULT_SECRET_FILES, *extra_files):
        merged.update(_parse_env_file(path))
    for key, val in merged.items():
        os.environ.setdefault(key, val)
    return merged


def get_secret(key: str, default: str | None = None) -> str | None:
    if key not in os.environ:
        load_fleet_secrets()
    return os.environ.get(key, default)


@dataclass
class FleetConfig:
    """Resolved secrets/config for all integrations across the fleet."""

    database_url: str | None = None
    linear_api_key: str | None = None
    linear_team_id: str | None = None
    notion_api_key: str | None = None
    cloudflare_api_token: str | None = None
    cloudflare_account_id: str | None = None
    sentry_dsn: str | None = None
    sentry_environment: str = "development"
    upstash_redis_url: str | None = None
    upstash_redis_token: str | None = None
    lance_db_uri: str | None = None
    r2_bucket: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None

    @classmethod
    def load(cls) -> FleetConfig:
        load_fleet_secrets()
        return cls(
            database_url=(
                os.environ.get("AGENT_MEMORY_DATABASE_URL")
                or os.environ.get("DATABASE_URL")
            ),
            linear_api_key=os.environ.get("LINEAR_API_KEY"),
            linear_team_id=os.environ.get("LINEAR_TEAM_ID"),
            notion_api_key=os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN"),
            cloudflare_api_token=os.environ.get("CLOUDFLARE_API_TOKEN"),
            cloudflare_account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
            sentry_dsn=os.environ.get("SENTRY_DSN"),
            sentry_environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
            upstash_redis_url=os.environ.get("UPSTASH_REDIS_REST_URL"),
            upstash_redis_token=os.environ.get("UPSTASH_REDIS_REST_TOKEN"),
            lance_db_uri=os.environ.get("LANCE_DB_URI"),
            r2_bucket=os.environ.get("R2_BUCKET")
            or os.environ.get("AGENT_MEMORY_R2_BUCKET")
            or "agent-memory",
            r2_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
            r2_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
        )

    def status(self) -> dict[str, bool]:
        """Boolean presence map — safe to log (no secret values)."""
        return {
            "database_url": bool(self.database_url),
            "linear": bool(self.linear_api_key),
            "notion": bool(self.notion_api_key),
            "cloudflare": bool(self.cloudflare_api_token and self.cloudflare_account_id),
            "sentry": bool(self.sentry_dsn),
            "upstash": bool(self.upstash_redis_url and self.upstash_redis_token),
        }

    def redacted(self) -> dict[str, str]:
        """Masked summary for logging."""

        def mask(v: str | None) -> str:
            return "set" if v else "(unset)"

        return {
            "database_url": re.sub(r":[^:@/]+@", ":***@", self.database_url or "(unset)"),
            "linear_api_key": mask(self.linear_api_key),
            "notion_api_key": mask(self.notion_api_key),
            "cloudflare_api_token": mask(self.cloudflare_api_token),
            "cloudflare_account_id": mask(self.cloudflare_account_id),
            "sentry_dsn": "set" if self.sentry_dsn else "(unset)",
            "lance_db_uri": mask(self.lance_db_uri),
        }
