"""Wrapper to expose MCP tools as Athena tools."""

from typing import Any, List

from athena.models.tool import Tool, ToolParameter, ToolResult
from .client import MCPClient
from .schema_converter import convert_json_schema_to_tool_parameters


class MCPToolWrapper(Tool):
    """Wraps an MCP tool as an Athena Tool."""

    def __init__(
        self,
        mcp_client: MCPClient,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any]
    ):
        self.mcp_client = mcp_client
        self._name = f"{mcp_client.server_name}:{tool_name}"
        self._description = f"[MCP:{mcp_client.server_name}] {tool_description}"
        self._parameters = convert_json_schema_to_tool_parameters(input_schema)
        self.mcp_tool_name = tool_name  # Original tool name for MCP calls

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> List[ToolParameter]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the MCP tool."""
        try:
            # Call the MCP server tool
            result = await self.mcp_client.call_tool(
                self.mcp_tool_name,
                kwargs
            )

            # Extract content from MCP response
            content_items = result.get("content", [])
            output_parts = []
            for item in content_items:
                if item.get("type") == "text":
                    output_parts.append(item.get("text", ""))

            output = "\n".join(output_parts)
            is_error = result.get("isError", False)

            return ToolResult(
                success=not is_error,
                output=output,
                error=output if is_error else None,
                metadata={"mcp_server": self.mcp_client.server_name}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"MCP tool execution failed: {str(e)}",
                metadata={"mcp_server": self.mcp_client.server_name}
            )
