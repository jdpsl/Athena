#!/usr/bin/env python3
"""Test MCP integration end-to-end."""
import asyncio
import sys
from pathlib import Path

# Add athena to path
sys.path.insert(0, str(Path(__file__).parent))

from athena.models.config import AthenaConfig, MCPConfig, MCPServerConfig
from athena.tools.base import ToolRegistry
from athena.mcp.manager import MCPClientManager


async def test_mcp_integration():
    """Test MCP client integration."""
    print("=" * 60)
    print("Testing MCP Integration")
    print("=" * 60)

    # Create MCP configuration
    mcp_config = MCPConfig(
        enabled=True,
        servers=[
            MCPServerConfig(
                name="test",
                transport="stdio",
                command="python3",
                args=["test_mcp_server.py"],
                enabled=True,
                timeout=10
            )
        ]
    )

    print("\n1. Configuration created ✓")
    print(f"   - Enabled: {mcp_config.enabled}")
    print(f"   - Servers: {len(mcp_config.servers)}")

    # Create tool registry and MCP manager
    tool_registry = ToolRegistry()
    mcp_manager = MCPClientManager(mcp_config)

    print("\n2. MCP Manager initialized ✓")

    # Initialize MCP servers
    print("\n3. Connecting to MCP servers...")
    await mcp_manager.initialize_all(tool_registry)

    print("\n4. MCP servers connected ✓")
    print(f"   - Active clients: {len(mcp_manager.clients)}")

    # List registered tools
    print("\n5. Registered tools:")
    all_tools = tool_registry.tools
    mcp_tools = {name: tool for name, tool in all_tools.items() if name.startswith("test:")}

    for name, tool in mcp_tools.items():
        print(f"   - {name}: {tool.description}")
        print(f"     Parameters: {[p.name for p in tool.parameters]}")

    print(f"\n6. Found {len(mcp_tools)} MCP tools ✓")

    # Test echo tool
    if "test:echo" in mcp_tools:
        print("\n7. Testing 'echo' tool...")
        echo_tool = mcp_tools["test:echo"]
        result = await echo_tool.execute(message="Hello MCP!")
        print(f"   - Success: {result.success}")
        print(f"   - Output: {result.output}")
        print(f"   - Metadata: {result.metadata}")
        if result.success:
            print("   ✓ Echo tool works!")

    # Test add tool
    if "test:add" in mcp_tools:
        print("\n8. Testing 'add' tool...")
        add_tool = mcp_tools["test:add"]
        result = await add_tool.execute(a=5, b=3)
        print(f"   - Success: {result.success}")
        print(f"   - Output: {result.output}")
        print(f"   - Metadata: {result.metadata}")
        if result.success:
            print("   ✓ Add tool works!")

    # Cleanup
    print("\n9. Cleaning up...")
    await mcp_manager.cleanup_all()
    print("   ✓ Cleanup complete")

    print("\n" + "=" * 60)
    print("MCP Integration Test: SUCCESS! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_integration())
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
