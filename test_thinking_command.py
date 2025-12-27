#!/usr/bin/env python3
"""Test the /thinking command."""

import asyncio
from athena.cli import AthenaSession
from athena.models.config import AthenaConfig

async def test_thinking_command():
    """Test /thinking slash command."""
    config = AthenaConfig()
    session = AthenaSession(config)
    await session.initialize()

    print("Testing /thinking command:\n")

    # Test initial state
    print(f"Initial state: enable_thinking = {session.config.agent.enable_thinking}")
    assert session.config.agent.enable_thinking == True, "Default should be True"

    # Test disable
    print("\nExecuting: /thinking off")
    await session._handle_command("/thinking off")
    print(f"After disable: enable_thinking = {session.config.agent.enable_thinking}")
    assert session.config.agent.enable_thinking == False, "Should be disabled"

    # Test enable
    print("\nExecuting: /thinking on")
    await session._handle_command("/thinking on")
    print(f"After enable: enable_thinking = {session.config.agent.enable_thinking}")
    assert session.config.agent.enable_thinking == True, "Should be enabled"

    # Test status display
    print("\nExecuting: /thinking")
    await session._handle_command("/thinking")

    print("\n" + "="*60)
    print("✅ All tests passed!")

    await session.cleanup()

if __name__ == "__main__":
    asyncio.run(test_thinking_command())
