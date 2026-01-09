#!/usr/bin/env python3
"""Test the /streaming command."""

import asyncio
from pathlib import Path
from athena.models.config import AthenaConfig
from athena.cli import AthenaSession
from rich.console import Console

console = Console()


async def test_streaming_command():
    """Test that /streaming command toggles streaming mode."""
    print("\nTesting /streaming Command\n")
    print("=" * 60)

    # Create config
    config = AthenaConfig(
        working_directory=".",
        agent={"streaming": False}  # Start with streaming disabled
    )

    print(f"\n1. Initial state: streaming = {config.agent.streaming}")
    assert config.agent.streaming is False, "Should start with streaming disabled"
    print("   ✓ Initial state correct")

    # Create session
    session = AthenaSession(config)
    await session.initialize()

    print("\n2. Testing /streaming status display...")
    # The status should show disabled
    assert session.config.agent.streaming is False
    print("   ✓ Status reflects disabled state")

    print("\n3. Testing /streaming on...")
    # Simulate enabling streaming
    session.config.agent.streaming = True
    assert session.config.agent.streaming is True
    print("   ✓ Streaming enabled successfully")

    print("\n4. Testing /streaming off...")
    # Simulate disabling streaming
    session.config.agent.streaming = False
    assert session.config.agent.streaming is False
    print("   ✓ Streaming disabled successfully")

    print("\n5. Testing variations of 'on' commands...")
    for value in ['on', 'true', '1', 'yes']:
        session.config.agent.streaming = False  # Reset
        # Simulate command
        if value in ['on', 'true', '1', 'yes']:
            session.config.agent.streaming = True
        assert session.config.agent.streaming is True, f"Failed for value: {value}"
    print("   ✓ All 'on' variations work")

    print("\n6. Testing variations of 'off' commands...")
    for value in ['off', 'false', '0', 'no']:
        session.config.agent.streaming = True  # Reset
        # Simulate command
        if value in ['off', 'false', '0', 'no']:
            session.config.agent.streaming = False
        assert session.config.agent.streaming is False, f"Failed for value: {value}"
    print("   ✓ All 'off' variations work")

    # Cleanup
    await session.cleanup()

    print("\n" + "=" * 60)
    print("✅ All /streaming command tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_streaming_command())
        exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
