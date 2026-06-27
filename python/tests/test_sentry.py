"""Tests for dreaming-memory Sentry integration."""

import sys
from unittest.mock import MagicMock, patch

from dreaming_memory.config import FleetConfig
from dreaming_memory.observability.sentry import breadcrumb, init_sentry


def test_init_sentry_no_dsn():
    config = FleetConfig(sentry_dsn=None)
    result = init_sentry(config)
    assert result is False


def test_init_sentry_with_dsn():
    config = FleetConfig(sentry_dsn="https://test@sentry.io/123")
    mock_sdk = MagicMock()
    with patch.dict(sys.modules, {"sentry_sdk": mock_sdk}):
        result = init_sentry(config)
        assert result is True
        mock_sdk.init.assert_called_once()


def test_init_sentry_import_error():
    config = FleetConfig(sentry_dsn="https://test@sentry.io/123")
    with patch.dict(sys.modules, {"sentry_sdk": None}):
        result = init_sentry(config)
        assert result is False


def test_breadcrumb_inactive():
    # _ACTIVE is False by default
    breadcrumb("test message")  # Should not raise


def test_breadcrumb_active():
    import dreaming_memory.observability.sentry as sentry_mod
    original = sentry_mod._ACTIVE
    sentry_mod._ACTIVE = True
    mock_sdk = MagicMock()
    try:
        with patch.dict(sys.modules, {"sentry_sdk": mock_sdk}):
            breadcrumb("test message", data={"key": "value"})
            mock_sdk.add_breadcrumb.assert_called_once()
    finally:
        sentry_mod._ACTIVE = original
