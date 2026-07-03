from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    output: str
    data: dict[str, Any] = {}


class Tool(ABC):
    """Base class for a pluggable tool.

    Tools are the only thing that touches the outside world (filesystem,
    shell, Docker, git, ...). Agents never do this directly — they call
    ``governance.permissions.invoke_tool_for_agent(agent_key, tool_key, action,
    **kwargs)``, which checks the agent's ``allowed_tools``, calls the tool,
    and writes an audit log entry. This is also the seam where a local tool
    gets swapped for an MCP-backed one later without touching agent code.
    """

    key: str
    description: str

    @abstractmethod
    def run(self, action: str, **kwargs: Any) -> ToolResult: ...
