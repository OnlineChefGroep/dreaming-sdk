"""Slack integration for reporting agent memory events."""

from __future__ import annotations

import os
from typing import Any

import httpx


class SlackClient:
    """Lightweight Slack Webhook client for reporting eval results."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")

    def post_message(self, text: str, blocks: list[dict[str, Any]] | None = None) -> None:
        if not self.webhook_url:
            return
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        resp = httpx.post(self.webhook_url, json=payload, timeout=10.0)
        resp.raise_for_status()

    def report_eval_result(self, metrics: dict[str, Any], run_id: str | None = None) -> None:
        """Post a formatted eval summary to Slack."""
        faithfulness = metrics.get("faithfulness_score", "N/A")
        precision = metrics.get("precision", "N/A")
        recall = metrics.get("recall", "N/A")

        try:
            val = float(faithfulness)
            status_emoji = "✅" if val > 0.6 else "⚠️"
        except (ValueError, TypeError):
            status_emoji = "❓"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{status_emoji} Dream Eval Result"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id or 'unknown'}"},
                    {"type": "mrkdwn", "text": f"*Faithfulness:*\n{faithfulness}"},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Precision:*\n{precision}"},
                    {"type": "mrkdwn", "text": f"*Recall:*\n{recall}"},
                ],
            },
        ]

        self.post_message(f"Dream Eval Result: {faithfulness}", blocks=blocks)
