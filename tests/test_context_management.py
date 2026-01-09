#!/usr/bin/env python3
"""Test context management."""

import asyncio
from athena.context.manager import ContextManager
from athena.context.compressor import MessageCompressor
from athena.models.message import Message, Role


async def test_context_manager():
    """Test context manager."""
    print("\nTesting Context Manager\n")
    print("=" * 60)

    manager = ContextManager(max_tokens=1000)

    # Test 1: Small context (no compression needed)
    messages = [Message(role=Role.USER, content="Hello")]
    assert not manager.should_compress(messages)
    print("✓ Small context doesn't trigger compression")

    # Test 2: Large context (needs compression)
    large_content = "x" * 4000  # ~1000 tokens
    messages = [Message(role=Role.USER, content=large_content)]
    assert manager.should_compress(messages)
    print("✓ Large context triggers compression")

    # Test 3: Stats
    stats = manager.get_compression_stats(messages)
    print(f"✓ Stats: {stats['current_tokens']} tokens, "
          f"{stats['utilization']:.1%} utilization")

    # Test 4: Token estimation
    test_messages = [
        Message(role=Role.SYSTEM, content="System prompt"),
        Message(role=Role.USER, content="User query"),
        Message(role=Role.ASSISTANT, content="Assistant response"),
    ]
    tokens = manager.estimate_tokens(test_messages)
    print(f"✓ Token estimation: {tokens} tokens for 3 messages")

    print("=" * 60)
    print("✅ Context manager tests passed\n")


async def test_message_compressor():
    """Test message compressor."""
    print("\nTesting Message Compressor\n")
    print("=" * 60)

    compressor = MessageCompressor()

    # Create message sequence
    messages = [
        Message(role=Role.SYSTEM, content="System prompt"),
    ]

    for i in range(20):
        messages.append(Message(role=Role.USER, content=f"User message {i}"))
        messages.append(Message(role=Role.ASSISTANT, content=f"Assistant response {i}"))

    print(f"Original: {len(messages)} messages")

    # Compress
    compressed = await compressor.compress(messages, keep_recent=10)

    print(f"Compressed: {len(compressed)} messages")
    print(f"  - System message: {'✓' if compressed[0].role == Role.SYSTEM else '✗'}")
    print(f"  - Summary message: {'✓' if 'summary' in compressed[1].content.lower() else '✗'}")
    print(f"  - Recent messages preserved: {'✓' if len(compressed) == 12 else '✗'}")

    assert len(compressed) == 12  # 1 system + 1 summary + 10 recent
    assert compressed[0].role == Role.SYSTEM
    assert "summary" in compressed[1].content.lower()

    print(f"\nSummary content: {compressed[1].content}")

    print("=" * 60)
    print("✅ Message compressor tests passed\n")


async def test_compression_with_tool_calls():
    """Test compression with tool calls."""
    print("\nTesting Compression with Tool Calls\n")
    print("=" * 60)

    from athena.models.message import ToolCall

    compressor = MessageCompressor()

    messages = [
        Message(role=Role.SYSTEM, content="System"),
        Message(role=Role.USER, content="Query 1"),
        Message(
            role=Role.ASSISTANT,
            content="Using tool",
            tool_calls=[
                ToolCall(id="1", name="Read", parameters={"file": "test.py"})
            ]
        ),
        Message(role=Role.TOOL, content="File contents...", tool_call_id="1", name="Read"),
        Message(role=Role.USER, content="Query 2"),
        Message(role=Role.ASSISTANT, content="Response 2"),
    ]

    print(f"Original: {len(messages)} messages with tool calls")

    compressed = await compressor.compress(messages, keep_recent=3)

    print(f"Compressed: {len(compressed)} messages")
    print(f"  - Contains 'Read' in summary: {'✓' if 'Read' in compressed[1].content else '✗'}")

    assert "Read" in compressed[1].content  # Tool name should be in summary

    print("=" * 60)
    print("✅ Tool call compression tests passed\n")


async def test_no_compression_needed():
    """Test when compression is not needed."""
    print("\nTesting No Compression Needed\n")
    print("=" * 60)

    compressor = MessageCompressor()

    # Only a few messages
    messages = [
        Message(role=Role.SYSTEM, content="System"),
        Message(role=Role.USER, content="Query"),
        Message(role=Role.ASSISTANT, content="Response"),
    ]

    compressed = await compressor.compress(messages, keep_recent=10)

    print(f"Original: {len(messages)} messages")
    print(f"Compressed: {len(compressed)} messages")
    print(f"  - Same length: {'✓' if len(messages) == len(compressed) else '✗'}")

    assert len(messages) == len(compressed)  # Should be unchanged

    print("=" * 60)
    print("✅ No-compression test passed\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CONTEXT MANAGEMENT MODULE TESTS")
    print("=" * 60)

    await test_context_manager()
    await test_message_compressor()
    await test_compression_with_tool_calls()
    await test_no_compression_needed()

    print("\n" + "=" * 60)
    print("✅ ALL CONTEXT MANAGEMENT TESTS PASSED!")
    print("=" * 60)
    print("\nContext module is ready:")
    print("  • ContextManager - tracks tokens and triggers compression")
    print("  • MessageCompressor - summarizes old messages")
    print("  • Preserves system message + recent N messages")
    print("  • Compresses middle messages into summary")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
        exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
