"""Base tool registry."""

from typing import Any, Optional
from athena.models.tool import Tool, ToolResult
from athena.errors.recovery import ErrorRecovery


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self, enable_error_recovery: bool = True):
        """Initialize tool registry.

        Args:
            enable_error_recovery: Whether to enable automatic error recovery for tools
        """
        self.tools: dict[str, Tool] = {}
        self.error_recovery = ErrorRecovery(enable_recovery=enable_error_recovery)

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self.tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools.

        Returns:
            List of all tools
        """
        return list(self.tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert all tools to OpenAI format.

        Returns:
            List of tool definitions
        """
        return [tool.to_openai_tool_dict() for tool in self.tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name with automatic error recovery.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            Tool result
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' not found",
            )

        # Tools that should NOT be retried (state-changing operations)
        non_retryable_tools = {
            "Write", "Edit", "Insert", "Delete", "Move", "Copy", "MakeDir",
            "GitCommit", "GitPush",
        }

        # Only use error recovery for read-only tools
        if name in non_retryable_tools:
            # Execute without retry for state-changing operations
            try:
                return await tool.execute(**kwargs)
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Tool execution failed: {str(e)}",
                )
        else:
            # Execute with error recovery for read-only operations
            try:
                return await self.error_recovery.execute_with_recovery(
                    tool.execute,
                    **kwargs,
                    operation_name=f"{name} tool"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Tool execution failed: {str(e)}",
                )
