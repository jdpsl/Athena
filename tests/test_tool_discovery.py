"""Test tool auto-discovery system."""

import asyncio
from athena.tools.base import ToolRegistry


async def test_tool_discovery():
    """Test the tool auto-discovery functionality."""

    # Create a fresh tool registry
    registry = ToolRegistry()

    # Test auto-discovery
    print("Testing tool auto-discovery...")
    discovered = registry.auto_discover_tools()

    print(f"\n✓ Discovered {len(discovered)} tools:")
    for tool_name in sorted(discovered):
        print(f"  • {tool_name}")

    # List all tools
    print(f"\n✓ Total tools registered: {len(registry.list_tools())}")

    # Test disabling a tool
    print("\n---\nTesting tool disable/enable...")
    if "Read" in registry.tools:
        print("✓ Read tool found, disabling it...")
        registry.disable_tool("Read")
        print(f"  Read tool enabled: {registry.is_tool_enabled('Read')}")
        print(f"  Disabled tools: {registry.disabled_tools}")

        # Re-enable
        print("\n✓ Re-enabling Read tool...")
        registry.enable_tool("Read")
        print(f"  Read tool enabled: {registry.is_tool_enabled('Read')}")
        print(f"  Disabled tools: {registry.disabled_tools}")

    # Test get_tool_info
    print("\n---\nTesting get_tool_info...")
    if "Read" in registry.tools:
        info = registry.get_tool_info("Read")
        if info:
            print(f"✓ Tool info for '{info['name']}':")
            print(f"  Description: {info['description'][:60]}...")
            print(f"  Parameters: {len(info['parameters'])}")
            print(f"  Enabled: {info['enabled']}")

    # Test with disabled tools from start
    print("\n---\nTesting auto-discovery with disabled tools...")
    registry2 = ToolRegistry()
    disabled = {"Read", "Write", "Edit"}
    discovered2 = registry2.auto_discover_tools(disabled_tools=disabled)

    print(f"✓ Discovered {len(discovered2)} tools (with {len(disabled)} disabled)")
    print(f"  Disabled: {sorted(registry2.disabled_tools)}")
    print(f"  Registered: {len(registry2.list_tools())}")

    # Verify disabled tools are not registered
    for tool_name in disabled:
        if tool_name in registry2.tools:
            print(f"  ✗ ERROR: {tool_name} was registered despite being disabled!")
        else:
            print(f"  ✓ {tool_name} correctly not registered")

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_tool_discovery())
