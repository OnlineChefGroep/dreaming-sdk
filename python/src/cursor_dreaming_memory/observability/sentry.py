"""Optional Sentry instrumentation for the agent memory layer."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cursor_dreaming_memory.config import FleetConfig

_ACTIVE = False


def init_sentry(config: FleetConfig | None = None, dsn: str | None = None) -> bool:
    """Initialize Sentry if the SDK and a DSN are available. Returns True if active."""
    global _ACTIVE
    if config is not None:
        dsn = dsn or config.sentry_dsn
        environment = config.sentry_environment
    else:
        dsn = dsn or os.environ.get("SENTRY_DSN")
        environment = os.environ.get("SENTRY_ENVIRONMENT", "development")
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
    )
    _ACTIVE = True
    return True


def breadcrumb(message: str, data: dict[str, Any] | None = None, category: str = "memory") -> None:
    if not _ACTIVE:
        return
    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(category=category, message=message, data=data or {})
    except ImportError:
        pass


def capture(exc: BaseException) -> None:
    if not _ACTIVE:
        return
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass
