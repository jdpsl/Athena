"""Base MCP client interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class MCPTool(BaseModel):
    """MCP tool definition."""

    name: str
    description: str
    inputSchema: dict[str, Any]


class MCPClient(ABC):
    """Abstract base class for MCP clients."""

    def __init__(self, server_name: str, timeout: int = 30):
        self.server_name = server_name
        self.timeout = timeout
        self.request_id = 0
        self.initialized = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send JSON-RPC request and get response."""
        pass

    async def initialize(self, client_name: str = "athena", client_version: str = "1.0.0") -> dict:
        """Initialize MCP connection."""
        result = await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": client_name, "version": client_version}
        })
        self.initialized = True
        return result

    async def list_tools(self) -> list[MCPTool]:
        """Discover available tools from server."""
        response = await self.send_request("tools/list")
        tools_data = response.get("result", {}).get("tools", [])
        return [MCPTool(**tool) for tool in tools_data]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""
        response = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return response.get("result", {})
