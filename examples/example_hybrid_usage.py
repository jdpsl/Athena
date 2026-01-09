#!/usr/bin/env python3
"""Example demonstrating hybrid SQLite + Files approach.

This shows real-world use cases combining:
- SQLite: Job queue, dependencies, parallel coordination, analytics
- Files: Conversation history, session management, checkpoints
"""

import asyncio
from athena.orchestrator import TaskOrchestrator
from athena.models.message import Role


async def example_1_parallel_exploration():
    """Example 1: Run 3 explore agents in parallel, then summarize.

    This uses SQLite for:
    - Tracking parallel jobs
    - Managing dependencies (summary depends on explore tasks)
    - Coordinating execution
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Parallel Exploration with Dependencies")
    print("=" * 60)

    orchestrator = TaskOrchestrator()
    await orchestrator.initialize()

    # Run 3 explore tasks in parallel
    print("\n📋 Creating parallel exploration tasks...")
    job_ids = await orchestrator.run_parallel_tasks(
        tasks=[
            {
                "type": "explore",
                "payload": {"prompt": "Find all API endpoints in the codebase"}
            },
            {
                "type": "explore",
                "payload": {"prompt": "Find all database models"}
            },
            {
                "type": "explore",
                "payload": {"prompt": "Find all test files"}
            },
        ],
        then={
            "type": "main",
            "payload": {"prompt": "Summarize the architecture based on findings"}
        }
    )

    print(f"✓ Created {len(job_ids)} jobs:")
    for i, job_id in enumerate(job_ids[:-1], 1):
        print(f"  {i}. Explore task: {job_id}")
    print(f"  4. Summary task (depends on 1-3): {job_ids[-1]}")

    # Get job tree structure
    print("\n📊 Job dependency tree:")
    tree = await orchestrator.get_job_tree(job_ids[0])
    print(f"  Root: {tree['job']['type']} ({tree['job']['status']})")

    # In real usage, agents would claim and process these jobs
    print("\n💡 Benefit: SQLite tracks dependencies, enables parallel execution")

    await orchestrator.close()


async def example_2_conversation_sessions():
    """Example 2: Manage conversation sessions like Claude Code.

    This uses Files for:
    - Storing full conversation history
    - Quick session resume
    - Git-aware organization
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: File-Based Conversation Sessions")
    print("=" * 60)

    orchestrator = TaskOrchestrator()
    await orchestrator.initialize()

    # Create a new session (like starting `claude`)
    print("\n💬 Creating new conversation session...")
    session_id = orchestrator.create_conversation_session(
        name="Authentication Feature Implementation",
        tags=["feature", "auth"]
    )
    print(f"✓ Session created: {session_id}")
    print(f"  Stored in: .athena/sessions/{session_id}.json")

    # Add conversation messages
    print("\n📝 Adding messages to session...")
    orchestrator.add_message_to_session(
        session_id,
        Role.USER,
        "I need to implement user authentication with JWT tokens"
    )
    orchestrator.add_message_to_session(
        session_id,
        Role.ASSISTANT,
        "I'll help you implement JWT authentication. Let me explore the codebase first..."
    )
    print("✓ Added 2 messages")

    # Resume most recent session (like `claude --continue`)
    print("\n🔄 Resuming most recent session...")
    resumed_id = orchestrator.resume_most_recent_session()
    print(f"✓ Resumed: {resumed_id}")

    # Get conversation history
    history = orchestrator.get_conversation_history(session_id)
    print(f"\n📜 Conversation history ({len(history)} messages):")
    for msg in history:
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {msg.role.value}: {content_preview}")

    # List all sessions (like `claude --resume` picker)
    print("\n📋 All sessions:")
    sessions = orchestrator.list_sessions()
    for session in sessions:
        name = session['name'] or session['session_id'][:8]
        print(f"  • {name}: {session['message_count']} messages (branch: {session['git_branch']})")

    print("\n💡 Benefit: Files are simple, git-friendly, easy to browse")

    await orchestrator.close()


async def example_3_checkpointing():
    """Example 3: Checkpoint a long-running task.

    This uses both:
    - SQLite: Track job status and metadata
    - Files: Save message snapshots at intervals
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Checkpointing Long-Running Tasks")
    print("=" * 60)

    orchestrator = TaskOrchestrator()
    await orchestrator.initialize()

    # Create a long-running task with checkpointing
    print("\n⏳ Creating long-running planning task...")
    job_id = await orchestrator.create_task_with_checkpoints(
        task_type="plan",
        payload={"prompt": "Design a complete microservices architecture"},
        checkpoint_interval=5  # Checkpoint every 5 iterations
    )
    print(f"✓ Job created: {job_id}")
    print(f"  Checkpoints will be saved to: .athena/checkpoints/{job_id}-iterN.json")

    # Simulate saving checkpoints during execution
    print("\n💾 Simulating checkpoint saves...")
    from athena.models.message import Message

    for iteration in [5, 10, 15]:
        messages = [
            Message(role=Role.SYSTEM, content="System prompt"),
            Message(role=Role.USER, content="Design microservices"),
            Message(role=Role.ASSISTANT, content=f"Working on iteration {iteration}..."),
        ]

        orchestrator.save_task_checkpoint(job_id, iteration, messages)
        print(f"  ✓ Checkpoint saved at iteration {iteration}")

    # List checkpoints
    checkpoints = orchestrator.session_manager.list_checkpoints(job_id)
    print(f"\n📸 Available checkpoints ({len(checkpoints)}):")
    for cp in checkpoints:
        print(f"  • Iteration {cp['iteration']}: {cp['message_count']} messages ({cp['timestamp']})")

    # Resume from checkpoint (like after a crash)
    print("\n🔄 Resuming from latest checkpoint...")
    checkpoint_data = await orchestrator.resume_task_from_checkpoint(job_id)

    if checkpoint_data:
        print(f"✓ Resumed from iteration {checkpoint_data['iteration']}")
        print(f"  Messages restored: {len(checkpoint_data['messages'])}")
        print(f"  Job status: {checkpoint_data['job'].status.value}")

    print("\n💡 Benefit: Atomic file checkpoints + SQLite job tracking = resumable tasks")

    await orchestrator.close()


async def example_4_analytics():
    """Example 4: Query agent performance with SQL.

    This uses SQLite for:
    - Fast aggregation queries
    - Performance analytics
    - Debugging failed jobs
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Agent Performance Analytics (SQLite Power)")
    print("=" * 60)

    orchestrator = TaskOrchestrator()
    await orchestrator.initialize()

    # Get agent statistics
    print("\n📊 Agent performance statistics:")
    stats = await orchestrator.get_agent_statistics()

    print(f"  Total jobs: {stats['total_jobs']}")
    print(f"  Success rate: {stats['success_rate'] * 100:.1f}%")
    print("\n  By agent type:")
    for agent_type, data in stats['by_type'].items():
        print(f"    • {agent_type}: {data['count']} jobs, avg {data['avg_duration_ms']}ms")

    # Find failed jobs
    print("\n❌ Recent failures:")
    failures = await orchestrator.find_failed_jobs(limit=5)

    for failure in failures:
        print(f"  • [{failure['type']}] {failure['error']}")
        print(f"    Job ID: {failure['job_id']}")

    print("\n💡 Benefit: SQL enables instant analytics (vs scanning JSON files)")

    await orchestrator.close()


async def example_5_hybrid_workflow():
    """Example 5: Complete workflow using both systems.

    Real-world scenario: Multi-agent code review with conversation history.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Complete Hybrid Workflow")
    print("=" * 60)

    orchestrator = TaskOrchestrator()
    await orchestrator.initialize()

    # 1. Create a conversation session (FILE)
    print("\n1️⃣  Creating conversation session...")
    session_id = orchestrator.create_conversation_session(
        name="Code Review: PR #123",
        tags=["code-review", "pr-123"]
    )
    print(f"   ✓ Session: {session_id[:8]}... (stored in .athena/sessions/)")

    # 2. User sends initial request (FILE)
    print("\n2️⃣  User sends request...")
    orchestrator.add_message_to_session(
        session_id,
        Role.USER,
        "Review the authentication changes in PR #123"
    )

    # 3. Spawn parallel analysis tasks (SQLITE)
    print("\n3️⃣  Spawning parallel analysis agents...")
    job_ids = await orchestrator.run_parallel_tasks(
        tasks=[
            {"type": "explore", "payload": {"prompt": "Find security vulnerabilities"}},
            {"type": "explore", "payload": {"prompt": "Check code style issues"}},
            {"type": "test-runner", "payload": {"prompt": "Run test suite"}},
        ],
        then={
            "type": "code-reviewer",
            "payload": {"prompt": "Summarize code review findings"}
        }
    )
    print(f"   ✓ Created {len(job_ids)} jobs (tracked in athena.db)")

    # 4. Jobs execute (agents claim from SQLITE queue)
    print("\n4️⃣  Agents process jobs (simulated)...")
    print("   [ExploreAgent] Checking security...")
    print("   [ExploreAgent] Checking style...")
    print("   [TestRunnerAgent] Running tests...")
    print("   [CodeReviewAgent] Summarizing...")

    # 5. Results stored in conversation (FILE)
    print("\n5️⃣  Storing results in conversation...")
    orchestrator.add_message_to_session(
        session_id,
        Role.ASSISTANT,
        "Code review complete! Found 2 security issues and 5 style warnings. All tests pass."
    )

    # 6. User can resume later (FILE)
    print("\n6️⃣  Later: User resumes session...")
    resumed_id = orchestrator.resume_most_recent_session()
    history = orchestrator.get_conversation_history(resumed_id)
    print(f"   ✓ Resumed session with {len(history)} messages")

    # 7. Check job tree (SQLITE)
    print("\n7️⃣  Check job execution tree...")
    tree = await orchestrator.get_job_tree(job_ids[0])
    print(f"   ✓ Job tree: {tree['job']['type']} → {len(tree['children'])} children")

    print("\n" + "=" * 60)
    print("✅ HYBRID APPROACH BENEFITS:")
    print("=" * 60)
    print("  SQLite:")
    print("    • Fast job queries and filtering")
    print("    • Dependency tracking")
    print("    • Parallel agent coordination")
    print("    • Performance analytics")
    print()
    print("  Files:")
    print("    • Simple conversation storage")
    print("    • Git-friendly sessions")
    print("    • Easy manual inspection")
    print("    • Atomic checkpoints")
    print("=" * 60)

    await orchestrator.close()


async def main():
    """Run all examples."""
    print("\n🚀 ATHENA HYBRID STORAGE EXAMPLES")
    print("SQLite (job queue) + Files (sessions)")

    await example_1_parallel_exploration()
    await example_2_conversation_sessions()
    await example_3_checkpointing()
    await example_4_analytics()
    await example_5_hybrid_workflow()

    print("\n✅ All examples complete!")
    print("\nStorage locations:")
    print("  • SQLite: athena.db (job queue, dependencies, analytics)")
    print("  • Sessions: .athena/sessions/ (conversations)")
    print("  • Checkpoints: .athena/checkpoints/ (task snapshots)")


if __name__ == "__main__":
    asyncio.run(main())
