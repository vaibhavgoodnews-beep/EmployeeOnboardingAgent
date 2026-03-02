from __future__ import annotations

from typing import Any, Callable


class MCPRegistry:
    """Simple MCP-style tool registry for agent tool execution."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, function: Callable[..., Any]) -> None:
        if not name or not callable(function):
            raise ValueError("Tool name must be non-empty and function must be callable.")
        self._tools[name] = function

    def execute_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        payload = args or {}
        return self._tools[name](**payload)

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())
