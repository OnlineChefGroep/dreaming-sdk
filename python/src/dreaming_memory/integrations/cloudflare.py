"""Cloudflare R2 helper — optional remote backend for the LanceDB semantic layer.

R2 is S3-compatible. Configure via FleetConfig / env vars:
    CLOUDFLARE_ACCOUNT_ID
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET                (default: agent-memory)

Use `CloudflareR2(config).lance_uri()` as the LANCE_DB_URI so vectors live in R2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dreaming_memory.config import FleetConfig


class CloudflareR2:
    """Thin R2 (S3-compatible) helper bound to a FleetConfig."""

    def __init__(self, config: FleetConfig) -> None:
        self.config = config

    @property
    def configured(self) -> bool:
        return bool(
            self.config.cloudflare_account_id
            and self.config.r2_access_key_id
            and self.config.r2_secret_access_key
        )

    @property
    def endpoint(self) -> str:
        return f"https://{self.config.cloudflare_account_id}.r2.cloudflarestorage.com"

    def lance_uri(self, prefix: str = "lancedb") -> str | None:
        if not self.configured:
            return None
        return f"s3://{self.config.r2_bucket}/{prefix}"

    def storage_options(self) -> dict[str, str]:
        """Storage options for lancedb / pyarrow S3 filesystem against R2."""
        return {
            "aws_access_key_id": self.config.r2_access_key_id or "",
            "aws_secret_access_key": self.config.r2_secret_access_key or "",
            "aws_endpoint": self.endpoint,
            "aws_region": "auto",
        }

    def boto3_client(self):
        """Return a boto3 S3 client for R2 (requires the `r2` extra)."""
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.config.r2_access_key_id,
            aws_secret_access_key=self.config.r2_secret_access_key,
            region_name="auto",
        )
