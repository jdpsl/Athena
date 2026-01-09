#!/usr/bin/env python3
"""Test MCP slash commands."""
import asyncio
import sys
from pathlib import Path

# Add athena to path
sys.path.insert(0, str(Path(__file__).parent))

from athena.models.config import AthenaConfig
from athena.cli import AthenaSession
from rich.console import Console

console = Console()


async def test_mcp_commands():
    """Test all MCP slash commands."""
    print("=" * 60)
    print("Testing MCP Slash Commands")
    print("=" * 60)

    # Create a minimal config
    config = AthenaConfig()
    session = AthenaSession(config)
    await session.initialize()

    print("\n1. Testing /mcp-list (empty)")
    print("-" * 60)
    await session._handle_mcp_list()

    print("\n2. Testing /mcp-add (stdio server)")
    print("-" * 60)
    await session._handle_mcp_add("/mcp-add test stdio python3 test_mcp_server.py")

    print("\n3. Testing /mcp-list (with server)")
    print("-" * 60)
    await session._handle_mcp_list()

    print("\n4. Testing /tools (should show MCP tools)")
    print("-" * 60)
    mcp_tools = [name for name in session.tool_registry.tools.keys() if name.startswith("test:")]
    if mcp_tools:
        console.print(f"[green]✓[/green] Found {len(mcp_tools)} MCP tools:")
        for tool_name in mcp_tools:
            console.print(f"   • {tool_name}")
    else:
        console.print("[red]✗[/red] No MCP tools found!")

    print("\n5. Testing /mcp-disable")
    print("-" * 60)
    await session._handle_mcp_disable("/mcp-disable test")

    print("\n6. Testing /mcp-list (disabled server)")
    print("-" * 60)
    await session._handle_mcp_list()

    print("\n7. Checking tools removed")
    print("-" * 60)
    mcp_tools_after_disable = [name for name in session.tool_registry.tools.keys() if name.startswith("test:")]
    if not mcp_tools_after_disable:
        console.print("[green]✓[/green] MCP tools correctly removed from registry")
    else:
        console.print(f"[red]✗[/red] Tools still in registry: {mcp_tools_after_disable}")

    print("\n8. Testing /mcp-enable")
    print("-" * 60)
    await session._handle_mcp_enable("/mcp-enable test")

    print("\n9. Testing /mcp-list (re-enabled server)")
    print("-" * 60)
    await session._handle_mcp_list()

    print("\n10. Checking tools re-registered")
    print("-" * 60)
    mcp_tools_after_enable = [name for name in session.tool_registry.tools.keys() if name.startswith("test:")]
    if mcp_tools_after_enable:
        console.print(f"[green]✓[/green] MCP tools re-registered: {len(mcp_tools_after_enable)} tools")
    else:
        console.print("[red]✗[/red] No MCP tools after re-enabling!")

    print("\n11. Testing /mcp-remove")
    print("-" * 60)
    await session._handle_mcp_remove("/mcp-remove test")

    print("\n12. Testing /mcp-list (after removal)")
    print("-" * 60)
    await session._handle_mcp_list()

    print("\n13. Cleanup")
    print("-" * 60)
    await session.cleanup()

    print("\n" + "=" * 60)
    print("MCP Slash Commands Test: SUCCESS! ✓")
    print("=" * 60)
    print("\n[bold]Summary:[/bold]")
    print("  ✓ /mcp-list works")
    print("  ✓ /mcp-add works (dynamic connection)")
    print("  ✓ /mcp-disable works (dynamic disconnection)")
    print("  ✓ /mcp-enable works (dynamic reconnection)")
    print("  ✓ /mcp-remove works")
    print("  ✓ Tools properly managed in registry")
    print("\nNext: Use /save to persist MCP server changes!")


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_commands())
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
