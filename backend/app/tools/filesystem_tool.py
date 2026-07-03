from pathlib import Path
from typing import Any

from app.tools.base import Tool, ToolResult


class FilesystemTool(Tool):
    """Read/write/list files, sandboxed to a configured root directory.

    Every path is resolved and checked to be inside ``root`` — this is the
    safe local command execution boundary from the governance requirements.
    Path traversal outside the sandbox raises rather than silently clamping,
    so a bug in a caller fails loudly instead of quietly touching the wrong
    file.
    """

    key = "filesystem"
    description = "Read, write, and list files within the agent workspace sandbox."

    def __init__(self, root: str):
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        if self._root not in candidate.parents and candidate != self._root:
            raise PermissionError(f"Path '{relative_path}' escapes the sandbox root")
        return candidate

    def run(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "read_file":
            path = self._resolve(kwargs["path"])
            if not path.is_file():
                return ToolResult(success=False, output=f"No such file: {kwargs['path']}")
            return ToolResult(success=True, output=path.read_text(), data={"path": str(path)})

        if action == "write_file":
            path = self._resolve(kwargs["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(kwargs["content"])
            return ToolResult(
                success=True,
                output=f"Wrote {len(kwargs['content'])} bytes",
                data={"path": str(path)},
            )

        if action == "list_dir":
            path = self._resolve(kwargs.get("path", "."))
            entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
            return ToolResult(success=True, output="\n".join(entries), data={"entries": entries})

        return ToolResult(success=False, output=f"Unknown filesystem action: {action}")
