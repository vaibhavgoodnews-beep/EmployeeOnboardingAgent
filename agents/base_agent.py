from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    def __init__(self, mcp_registry: Any) -> None:
        self.mcp = mcp_registry

    @abstractmethod
    def plan(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def use_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def reflect(self, result: dict[str, Any]) -> dict[str, Any]:
        ...

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        planned_context = self.plan(context)
        tool_result = self.use_tools(planned_context)
        return self.reflect(tool_result)
