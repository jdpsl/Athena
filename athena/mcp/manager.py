"""Manager for MCP client connections and tool registration."""

import logging
from typing import List

from athena.models.config import MCPConfig, MCPServerConfig
from athena.tools.base import ToolRegistry
from .client import MCPClient
from .stdio_client import StdioMCPClient
from .http_client import HttpMCPClient
from .tool_wrapper import MCPToolWrapper

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages multiple MCP client connections and tool registration."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.clients: dict[str, MCPClient] = {}

    async def initialize_all(self, tool_registry: ToolRegistry) -> None:
        """Connect to all MCP servers and register their tools."""
        if not self.config.enabled:
            logger.info("MCP support is disabled")
            return

        for server_config in self.config.servers:
            if not server_config.enabled:
                logger.info(f"MCP server '{server_config.name}' is disabled, skipping")
                continue

            try:
                await self._initialize_server(server_config, tool_registry)
            except Exception as e:
                logger.error(f"Failed to initialize MCP server '{server_config.name}': {e}")

    async def _initialize_server(
        self,
        server_config: MCPServerConfig,
        tool_registry: ToolRegistry
    ) -> None:
        """Initialize a single MCP server and register its tools."""
        # Create client based on transport type
        client = self._create_client(server_config)

        # Connect and initialize
        await client.connect()
        await client.initialize()

        # Discover tools
        mcp_tools = await client.list_tools()
        logger.info(f"MCP server '{server_config.name}' provides {len(mcp_tools)} tools")

        # Wrap and register each tool
        for mcp_tool in mcp_tools:
            wrapper = MCPToolWrapper(
                mcp_client=client,
                tool_name=mcp_tool.name,
                tool_description=mcp_tool.description,
                input_schema=mcp_tool.inputSchema
            )
            tool_registry.register(wrapper)
            logger.info(f"Registered MCP tool: {wrapper.name}")

        # Store client for cleanup
        self.clients[server_config.name] = client

    def _create_client(self, server_config: MCPServerConfig) -> MCPClient:
        """Create appropriate client based on transport type."""
        if server_config.transport == "stdio":
            if not server_config.command:
                raise ValueError(f"MCP server '{server_config.name}': command required for stdio transport")
            return StdioMCPClient(
                server_name=server_config.name,
                command=server_config.command,
                args=server_config.args,
                env=server_config.env,
                timeout=server_config.timeout
            )
        elif server_config.transport == "http":
            if not server_config.url:
                raise ValueError(f"MCP server '{server_config.name}': url required for http transport")
            return HttpMCPClient(
                server_name=server_config.name,
                url=server_config.url,
                timeout=server_config.timeout
            )
        else:
            raise ValueError(f"Unknown transport type: {server_config.transport}")

    async def cleanup_all(self) -> None:
        """Disconnect all MCP clients."""
        for name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from MCP server '{name}'")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server '{name}': {e}")
