"""Tests for dreaming-memory dashboard module."""

from unittest.mock import MagicMock, patch


def test_get_metrics():
    with patch("dreaming_memory.dashboard._get_store") as mock_get:
        mock_store = MagicMock()
        mock_store.metrics.return_value = {"total": 10}
        mock_get.return_value = mock_store
        from dreaming_memory.dashboard import get_metrics
        result = get_metrics()
        assert result["total"] == 10


def test_bars():
    from dreaming_memory.dashboard import _bars
    rows = [{"key": "a", "count": 10}, {"key": "b", "count": 5}]
    result = _bars(rows, 20)
    assert "a" in result
    assert "b" in result


def test_bars_empty():
    from dreaming_memory.dashboard import _bars
    result = _bars([], 0)
    assert result == ""


def test_sparkline():
    from dreaming_memory.dashboard import _sparkline
    per_day = [{"day": "2026-01-01", "count": 10}, {"day": "2026-01-02", "count": 5}]
    result = _sparkline(per_day)
    assert "spark" in result


def test_sparkline_empty():
    from dreaming_memory.dashboard import _sparkline
    result = _sparkline([])
    assert "no data" in result


def test_render_html():
    from dreaming_memory.dashboard import render_html
    metrics = {
        "total": 100,
        "last_activity": "2026-01-01T00:00:00Z",
        "by_source": [],
        "by_memory_type": [],
        "by_session_type": [],
        "by_agent": [],
        "per_day": [],
        "triage_decisions": 5,
        "recent": [],
    }
    result = render_html(metrics)
    assert "100" in result
    assert "Agent Memory" in result


def test_get_store_singleton():
    with patch("dreaming_memory.dashboard._store", None):
        with patch("dreaming_memory.dashboard.AgentMemoryStore") as MockStore:
            mock_store = MagicMock()
            MockStore.return_value = mock_store
            from dreaming_memory.dashboard import _get_store
            result = _get_store()
            assert result is mock_store


def test_get_store_reuse():
    import dreaming_memory.dashboard as dash_mod
    original = dash_mod._store
    dash_mod._store = MagicMock()
    try:
        from dreaming_memory.dashboard import _get_store
        result = _get_store()
        assert result is dash_mod._store
    finally:
        dash_mod._store = original
