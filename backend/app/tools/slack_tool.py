from typing import Any

import httpx

from app.tools.base import Tool, ToolResult


class SlackNotifierTool(Tool):
    """Posts a message to a Slack incoming webhook.

    A concrete example of the "future tool categories" the architecture doc
    calls out (Slack/Jira/email/CRM/...) — a pluggable tool an agent calls
    the same way it calls any other, with no Slack SDK dependency (just an
    HTTP POST to a webhook URL). Gracefully returns a failed result rather
    than raising when no webhook is configured, so notifications being
    unset doesn't break whatever workflow tried to send one.
    """

    key = "slack"
    description = "Post a notification message to a configured Slack channel."

    def __init__(self, webhook_url: str | None, timeout_seconds: float = 10.0):
        self._webhook_url = webhook_url
        self._timeout = timeout_seconds

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action != "post_message":
            return ToolResult(success=False, output=f"Unknown slack action: {action}")

        if not self._webhook_url:
            return ToolResult(
                success=False,
                output="SLACK_WEBHOOK_URL is not configured — notification not sent.",
            )

        text = kwargs["text"]
        try:
            resp = httpx.post(self._webhook_url, json={"text": text}, timeout=self._timeout)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return ToolResult(success=False, output=f"Slack webhook request failed: {exc}")

        return ToolResult(success=True, output="Notification sent.")
