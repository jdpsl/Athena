#!/usr/bin/env python3
"""Test BaseAgent architecture and refactoring."""

import asyncio
from athena.models.config import AthenaConfig
from athena.tools.base import ToolRegistry
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.agent import MainAgent, ExploreAgent, PlanAgent, CodeReviewAgent, TestRunnerAgent
from athena.tools.file_ops import ReadTool, WriteTool, EditTool
from athena.tools.search import GlobTool, GrepTool
from athena.tools.bash import BashTool
from athena.tools.todo import TodoWriteTool


async def test_agent_tool_filtering():
    """Test that specialized agents get correct tools."""
    print("\nTesting Agent Tool Filtering\n")
    print("=" * 60)

    config = AthenaConfig(working_directory=".")
    job_queue = SQLiteJobQueue()
    await job_queue.initialize()

    # Create tool registry with multiple tools
    tool_registry = ToolRegistry()
    tool_registry.register(ReadTool())
    tool_registry.register(WriteTool())
    tool_registry.register(EditTool())
    tool_registry.register(GlobTool())
    tool_registry.register(GrepTool())
    tool_registry.register(BashTool())
    tool_registry.register(TodoWriteTool())

    print(f"Total tools in registry: {len(tool_registry.list_tools())}")

    # Test MainAgent - should get all tools
    main_agent = MainAgent(config, tool_registry, job_queue)
    main_tools = main_agent._get_filtered_tools()
    print(f"\n✓ MainAgent:")
    print(f"  - Allowed tools: All")
    print(f"  - Tools returned: {len(main_tools) if main_tools else 0}")
    assert main_tools is not None
    assert len(main_tools) == 7  # All 7 tools

    # Test ExploreAgent - should get only 3 tools
    explore_agent = ExploreAgent(config, tool_registry, job_queue)
    explore_tools = explore_agent._get_filtered_tools()
    print(f"\n✓ ExploreAgent:")
    print(f"  - Allowed tools: {explore_agent.get_allowed_tools()}")
    print(f"  - Tools returned: {len(explore_tools) if explore_tools else 0}")
    assert explore_tools is not None
    assert len(explore_tools) == 3  # Only Glob, Grep, Read
    tool_names = [t['function']['name'] for t in explore_tools]
    assert set(tool_names) == {"Glob", "Grep", "Read"}

    # Test PlanAgent - should get only 4 tools
    plan_agent = PlanAgent(config, tool_registry, job_queue)
    plan_tools = plan_agent._get_filtered_tools()
    print(f"\n✓ PlanAgent:")
    print(f"  - Allowed tools: {plan_agent.get_allowed_tools()}")
    print(f"  - Tools returned: {len(plan_tools) if plan_tools else 0}")
    assert plan_tools is not None
    assert len(plan_tools) == 4  # Glob, Grep, Read, TodoWrite
    tool_names = [t['function']['name'] for t in plan_tools]
    assert set(tool_names) == {"Glob", "Grep", "Read", "TodoWrite"}

    # Test CodeReviewAgent - should get only 4 tools
    review_agent = CodeReviewAgent(config, tool_registry, job_queue)
    review_tools = review_agent._get_filtered_tools()
    print(f"\n✓ CodeReviewAgent:")
    print(f"  - Allowed tools: {review_agent.get_allowed_tools()}")
    print(f"  - Tools returned: {len(review_tools) if review_tools else 0}")
    assert review_tools is not None
    assert len(review_tools) == 4  # Read, Grep, Glob, TodoWrite

    # Test TestRunnerAgent - should get only 4 tools
    test_agent = TestRunnerAgent(config, tool_registry, job_queue)
    test_tools = test_agent._get_filtered_tools()
    print(f"\n✓ TestRunnerAgent:")
    print(f"  - Allowed tools: {test_agent.get_allowed_tools()}")
    print(f"  - Tools returned: {len(test_tools) if test_tools else 0}")
    assert test_tools is not None
    assert len(test_tools) == 4  # Read, Grep, Glob, Bash

    await job_queue.close()

    print("\n" + "=" * 60)
    print("✅ Agent tool filtering tests passed!\n")


async def test_agent_type_names():
    """Test that agent type names are correct."""
    print("\nTesting Agent Type Names\n")
    print("=" * 60)

    config = AthenaConfig(working_directory=".")
    job_queue = SQLiteJobQueue()
    await job_queue.initialize()
    tool_registry = ToolRegistry()

    agents = [
        (MainAgent(config, tool_registry, job_queue), "main"),
        (ExploreAgent(config, tool_registry, job_queue), "explore"),
        (PlanAgent(config, tool_registry, job_queue), "plan"),
        (CodeReviewAgent(config, tool_registry, job_queue), "code-reviewer"),
        (TestRunnerAgent(config, tool_registry, job_queue), "test-runner"),
    ]

    for agent, expected_name in agents:
        actual_name = agent.get_agent_type_name()
        status = "✓" if actual_name == expected_name else "✗"
        print(f"{status} {agent.__class__.__name__}: '{actual_name}' (expected: '{expected_name}')")
        assert actual_name == expected_name

    await job_queue.close()

    print("=" * 60)
    print("✅ Agent type name tests passed!\n")


async def test_context_compression_integration():
    """Test that context compression works in agent loop."""
    print("\nTesting Context Compression Integration\n")
    print("=" * 60)

    from athena.models.message import Message, Role

    config = AthenaConfig(working_directory=".")
    job_queue = SQLiteJobQueue()
    await job_queue.initialize()
    tool_registry = ToolRegistry()

    agent = MainAgent(config, tool_registry, job_queue)

    # Create lots of messages to trigger compression
    for i in range(30):
        agent.messages.append(Message(role=Role.USER, content="x" * 1000))
        agent.messages.append(Message(role=Role.ASSISTANT, content="y" * 1000))

    print(f"Created {len(agent.messages)} messages")

    # Check if should compress
    should_compress = agent.context_manager.should_compress(agent.messages)
    print(f"Should compress: {should_compress}")
    assert should_compress

    # Compress
    compressed = await agent.message_compressor.compress(agent.messages, keep_recent=10)
    print(f"After compression: {len(compressed)} messages")
    print(f"  - Reduction: {len(agent.messages) - len(compressed)} messages removed")
    assert len(compressed) < len(agent.messages)
    assert len(compressed) <= 12  # 1 system (if exists) + 1 summary + 10 recent

    await job_queue.close()

    print("=" * 60)
    print("✅ Context compression integration tests passed!\n")


async def test_token_savings_calculation():
    """Calculate actual token savings from selective tools."""
    print("\nCalculating Token Savings\n")
    print("=" * 60)

    config = AthenaConfig(working_directory=".")
    job_queue = SQLiteJobQueue()
    await job_queue.initialize()

    # Create tool registry with all 7 test tools
    tool_registry = ToolRegistry()
    tool_registry.register(ReadTool())
    tool_registry.register(WriteTool())
    tool_registry.register(EditTool())
    tool_registry.register(GlobTool())
    tool_registry.register(GrepTool())
    tool_registry.register(BashTool())
    tool_registry.register(TodoWriteTool())

    def estimate_tool_tokens(tools):
        """Rough estimate of tokens for tool definitions."""
        if not tools:
            return 0
        # Each tool ~35 tokens on average (name + description + parameters)
        return len(tools) * 35

    # Calculate tokens for different agents
    main_agent = MainAgent(config, tool_registry, job_queue)
    main_tools = main_agent._get_filtered_tools()
    main_tokens = estimate_tool_tokens(main_tools)

    explore_agent = ExploreAgent(config, tool_registry, job_queue)
    explore_tools = explore_agent._get_filtered_tools()
    explore_tokens = estimate_tool_tokens(explore_tools)

    print(f"MainAgent tokens (all tools): ~{main_tokens}")
    print(f"ExploreAgent tokens (3 tools): ~{explore_tokens}")
    print(f"Savings per ExploreAgent call: ~{main_tokens - explore_tokens} tokens")
    print(f"Percentage saved: {((main_tokens - explore_tokens) / main_tokens * 100):.1f}%")

    await job_queue.close()

    print("=" * 60)
    print("✅ Token savings calculation complete!\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BASE AGENT ARCHITECTURE TESTS")
    print("=" * 60)

    await test_agent_tool_filtering()
    await test_agent_type_names()
    await test_context_compression_integration()
    await test_token_savings_calculation()

    print("\n" + "=" * 60)
    print("✅ ALL BASE AGENT ARCHITECTURE TESTS PASSED!")
    print("=" * 60)
    print("\nRefactoring Summary:")
    print("  • BaseAgent provides shared loop + context compression")
    print("  • MainAgent extends BaseAgent with all tools")
    print("  • Specialized agents get only relevant tools")
    print("  • ExploreAgent: 3 tools (saves ~140 tokens/call)")
    print("  • PlanAgent: 4 tools (saves ~105 tokens/call)")
    print("  • CodeReviewAgent: 4 tools (saves ~105 tokens/call)")
    print("  • TestRunnerAgent: 4 tools (saves ~105 tokens/call)")
    print("  • Context compression prevents overflow")
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
