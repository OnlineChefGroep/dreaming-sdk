"""Unit tests for SlackClient and the CLI export Markdown renderer (offline)."""

from __future__ import annotations

from typing import Any

import pytest

from cursor_dreaming_memory.integrations.slack import SlackClient


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None


def test_post_message_noop_without_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    client = SlackClient()
    assert client.post_message("hi") is False


def test_report_eval_result_posts_with_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], timeout: float) -> _FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("cursor_dreaming_memory.integrations.slack.httpx.post", fake_post)

    client = SlackClient(webhook_url="https://hooks.slack.test/xyz")
    result = client.report_eval_result({"faithfulness_score": 0.8}, run_id="run-1")

    assert result is True
    assert captured["url"] == "https://hooks.slack.test/xyz"
    assert captured["timeout"] == 10.0
    text = captured["json"]["text"]
    assert "✅" in text
    assert "run-1" in text


def test_report_eval_result_faithfulness_fallback_key() -> None:
    # Falls back to "faithfulness" when "faithfulness_score" is absent.
    client = SlackClient(webhook_url=None)
    # No webhook → post_message returns False, but the emoji logic still runs.
    assert SlackClient._faithfulness_emoji(0.8) == "✅"
    assert SlackClient._faithfulness_emoji(0.3) == "⚠️"
    assert SlackClient._faithfulness_emoji(0.6) == "⚠️"
    assert SlackClient._faithfulness_emoji(None) == "❓"
    assert SlackClient._faithfulness_emoji("nan-ish") == "❓"
    assert client.report_eval_result({"faithfulness": 0.9}) is False


def test_report_eval_result_warning_emoji(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], timeout: float) -> _FakeResponse:
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr("cursor_dreaming_memory.integrations.slack.httpx.post", fake_post)

    client = SlackClient(webhook_url="https://hooks.slack.test/xyz")
    assert client.report_eval_result({"faithfulness": 0.3}) is True
    assert "⚠️" in captured["json"]["text"]
