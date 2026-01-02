"""Base tool registry."""

import importlib
import inspect
from pathlib import Path
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
        self.disabled_tools: set[str] = set()  # Track disabled tool names

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

    def auto_discover_tools(self, disabled_tools: Optional[set[str]] = None) -> list[str]:
        """Auto-discover and register all tools from the athena/tools directory.

        Args:
            disabled_tools: Set of tool names that should not be registered

        Returns:
            List of discovered tool names
        """
        if disabled_tools:
            self.disabled_tools = disabled_tools

        discovered = []
        tools_dir = Path(__file__).parent

        # Find all Python files in tools directory
        for py_file in tools_dir.glob("*.py"):
            # Skip special files
            if py_file.name.startswith("_") or py_file.name == "base.py":
                continue

            module_name = f"athena.tools.{py_file.stem}"

            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Find all Tool subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a Tool subclass (but not Tool itself)
                    if (issubclass(obj, Tool) and
                        obj is not Tool and
                        obj.__module__ == module_name):

                        # Instantiate the tool
                        # Check if it needs special initialization
                        sig = inspect.signature(obj.__init__)
                        params = list(sig.parameters.keys())

                        # Skip 'self' parameter
                        if 'self' in params:
                            params.remove('self')

                        # Only instantiate if no required parameters
                        if not params or all(
                            sig.parameters[p].default != inspect.Parameter.empty
                            for p in params
                        ):
                            tool_instance = obj()
                            tool_name = tool_instance.name

                            # Only register if not disabled
                            if tool_name not in self.disabled_tools:
                                self.register(tool_instance)
                                discovered.append(tool_name)

            except Exception as e:
                # Skip modules that can't be imported or instantiated
                pass

        return discovered

    def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool.

        Args:
            tool_name: Name of the tool to enable

        Returns:
            True if tool was enabled, False if tool doesn't exist
        """
        if tool_name in self.disabled_tools:
            self.disabled_tools.remove(tool_name)
            # Try to re-discover and register this specific tool
            self.auto_discover_tools(self.disabled_tools)
            return True
        return tool_name in self.tools

    def disable_tool(self, tool_name: str) -> bool:
        """Disable a tool.

        Args:
            tool_name: Name of the tool to disable

        Returns:
            True if tool was disabled, False if tool doesn't exist
        """
        if tool_name in self.tools:
            self.disabled_tools.add(tool_name)
            del self.tools[tool_name]
            return True
        return False

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled.

        Args:
            tool_name: Name of the tool

        Returns:
            True if enabled, False otherwise
        """
        return tool_name in self.tools and tool_name not in self.disabled_tools

    def get_tool_info(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dict with tool info or None if not found
        """
        tool = self.get(tool_name)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type.value,
                        "description": p.description,
                        "required": p.required,
                    }
                    for p in tool.parameters
                ],
                "enabled": self.is_tool_enabled(tool_name),
            }
        return None
