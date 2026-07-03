import httpx

from app.tools.slack_tool import SlackNotifierTool


def test_unknown_action_fails():
    tool = SlackNotifierTool(webhook_url="https://hooks.slack.test/whatever")
    result = tool.run("not_post_message", text="hi")
    assert not result.success


def test_no_webhook_configured_fails_gracefully():
    tool = SlackNotifierTool(webhook_url=None)
    result = tool.run("post_message", text="hi")
    assert not result.success
    assert "not configured" in result.output


def test_post_message_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

    monkeypatch.setattr("app.tools.slack_tool.httpx.post", lambda *a, **kw: FakeResponse())

    tool = SlackNotifierTool(webhook_url="https://hooks.slack.test/whatever")
    result = tool.run("post_message", text="deploy finished")
    assert result.success


def test_post_message_http_error_returns_failed_result(monkeypatch):
    def raise_error(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr("app.tools.slack_tool.httpx.post", raise_error)

    tool = SlackNotifierTool(webhook_url="https://hooks.slack.test/whatever")
    result = tool.run("post_message", text="hi")
    assert not result.success
    assert "boom" in result.output
