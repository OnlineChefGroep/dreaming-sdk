"""Slack incoming-webhook client — post eval reports without external SDKs."""

from __future__ import annotations

import os
from typing import Any

import httpx

SLACK_TIMEOUT = 10.0


class SlackClient:
    """Minimal Slack incoming-webhook client (no Slack SDK dependency)."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")

    def post_message(
        self,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Post a message to the configured webhook.

        Returns False (no-op) when no webhook is configured so callers can run
        safely offline; otherwise POSTs and returns True on success.
        """
        if not self.webhook_url:
            return False
        payload: dict[str, Any] = {"text": text}
        if blocks is not None:
            payload["blocks"] = blocks
        resp = httpx.post(self.webhook_url, json=payload, timeout=SLACK_TIMEOUT)
        resp.raise_for_status()
        return True

    def report_eval_result(
        self,
        metrics: dict[str, Any],
        run_id: str | None = None,
    ) -> bool:
        """Format eval metrics into Slack blocks and post them."""
        faithfulness = metrics.get("faithfulness_score")
        if faithfulness is None:
            faithfulness = metrics.get("faithfulness")
        precision = metrics.get("precision_score", metrics.get("precision"))
        recall = metrics.get("recall_score", metrics.get("recall"))

        emoji = self._faithfulness_emoji(faithfulness)
        header = f"{emoji} Eval result"
        if run_id:
            header += f" — `{run_id}`"

        fields = [
            f"*Faithfulness:* {self._fmt(faithfulness)}",
            f"*Precision:* {self._fmt(precision)}",
            f"*Recall:* {self._fmt(recall)}",
        ]
        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header},
            },
            {
                "type": "section",
                "fields": [{"type": "mrkdwn", "text": f} for f in fields],
            },
        ]
        text = f"{header} | " + " | ".join(fields)
        return self.post_message(text, blocks=blocks)

    @staticmethod
    def _faithfulness_emoji(faithfulness: Any) -> str:
        """✅ when faithfulness > 0.6, ⚠️ when <= 0.6, ❓ when unparseable."""
        try:
            value = float(faithfulness)
        except (TypeError, ValueError):
            return "❓"
        return "✅" if value > 0.6 else "⚠️"

    @staticmethod
    def _fmt(value: Any) -> str:
        try:
            return f"{float(value):.3f}"
        except (TypeError, ValueError):
            return "n/a"
