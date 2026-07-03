from __future__ import annotations

from app.config import get_settings
from app.tools.base import Tool
from app.tools.coding_worker_tool import CodingWorkerTool
from app.tools.docker_tool import DockerTool
from app.tools.filesystem_tool import FilesystemTool
from app.tools.git_tool import GitTool
from app.tools.github_tool import GitHubTool
from app.tools.knowledge_tool import KnowledgeSearchTool
from app.tools.qa_runner_tool import QATestRunnerTool
from app.tools.slack_tool import SlackNotifierTool
from app.tools.terminal_tool import TerminalTool


class ToolRegistry:
    """Pluggable tool registry, keyed by tool key.

    Agents never instantiate tools directly — they're resolved here by key
    so a tool's implementation (local filesystem today, a remote/MCP-backed
    tool tomorrow) can change without touching agent or graph code.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.key] = tool

    def get(self, key: str) -> Tool:
        if key not in self._tools:
            raise KeyError(f"Unknown tool key: {key}")
        return self._tools[key]

    def list(self) -> list[Tool]:
        return list(self._tools.values())


def build_default_tool_registry() -> ToolRegistry:
    settings = get_settings()
    registry = ToolRegistry()
    registry.register(FilesystemTool(root=settings.workspace_root))
    registry.register(TerminalTool(cwd=settings.workspace_root))
    registry.register(GitTool(repo_dir=settings.workspace_root))
    registry.register(DockerTool(cwd=settings.workspace_root))
    registry.register(KnowledgeSearchTool())
    registry.register(GitHubTool(cwd=settings.workspace_root))
    registry.register(QATestRunnerTool())
    registry.register(CodingWorkerTool(backend=settings.coding_worker_backend))
    registry.register(SlackNotifierTool(webhook_url=settings.slack_webhook_url))
    return registry


tool_registry = build_default_tool_registry()
