"""Base agent with shared functionality."""

import uuid
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
from rich.console import Console
from athena.models.message import Message, Role, ToolCall
from athena.models.config import AthenaConfig
from athena.models.job import Job, JobStatus
from athena.llm.client import LLMClient
from athena.llm.thinking_injector import ThinkingInjector
from athena.llm.fallback_parser import FallbackToolParser
from athena.tools.base import ToolRegistry
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.context.manager import ContextManager
from athena.context.compressor import MessageCompressor
from athena.agent.retry_tracker import RetryTracker
from athena.models.permission import PermissionMode, get_allowed_tools_for_mode

console = Console()


class BaseAgent(ABC):
    """Base agent with context management and execution loop."""

    def __init__(
        self,
        config: AthenaConfig,
        tool_registry: ToolRegistry,
        job_queue: SQLiteJobQueue,
        session_manager: Optional[Any] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        """Initialize base agent.

        Args:
            config: Athena configuration
            tool_registry: Tool registry
            job_queue: Job queue
            session_manager: Optional session manager for conversation persistence
            context_manager: Optional context manager (creates default if None)
        """
        self.config = config
        self.tool_registry = tool_registry
        self.job_queue = job_queue
        self.session_manager = session_manager
        self.agent_id = str(uuid.uuid4())

        # Context management
        self.context_manager = context_manager or ContextManager(
            max_tokens=config.agent.context_max_tokens,
            compression_threshold=config.agent.context_compression_threshold
        )
        self.message_compressor = MessageCompressor()

        # Initialize LLM client
        thinking_injector = ThinkingInjector(
            enable_thinking=config.agent.enable_thinking,
            thinking_budget=config.agent.thinking_budget,
        )
        self.llm_client = LLMClient(config.llm, thinking_injector)

        # Initialize fallback parser if needed
        self.fallback_parser = FallbackToolParser() if config.agent.fallback_mode else None

        # Retry tracking for loop prevention
        self.retry_tracker = RetryTracker(
            max_retries=getattr(config.agent, 'max_retries', 3),
            failure_limit=getattr(config.agent, 'failure_limit', 5)
        )

        # Stop control
        self.stop_requested = False

        # Conversation history
        self.messages: list[Message] = []

    @abstractmethod
    def get_agent_type_name(self) -> str:
        """Get agent type name for logging.

        Returns:
            Agent type name (e.g., "main", "explore", "plan")
        """
        pass

    @abstractmethod
    def get_allowed_tools(self) -> Optional[list[str]]:
        """Get list of allowed tool names.

        Returns:
            List of tool names, or None for all tools
        """
        pass

    def request_stop(self):
        """Request the agent to stop after current operation."""
        self.stop_requested = True

    async def _save_message(self, message: Message) -> None:
        """Save message to conversation history and database.

        Args:
            message: Message to save
        """
        self.messages.append(message)

        # Save to database if session manager is available
        if self.session_manager:
            try:
                sequence = len(self.messages) - 1
                await self.session_manager.save_message(message, sequence)
            except Exception as e:
                # Don't fail if saving fails, just log
                console.print(f"[dim yellow]Warning: Failed to save message to database: {e}[/dim yellow]")

    def _get_filtered_tools(self) -> Optional[list[dict]]:
        """Get filtered tools based on allowed_tools and permission mode.

        Returns:
            List of tool definitions in OpenAI format, or None for all tools
        """
        # In fallback mode, don't send tools to API
        if self.config.agent.fallback_mode:
            return None

        # Get base allowed tools (from agent type)
        allowed = self.get_allowed_tools()

        # Get all tool names
        all_tool_names = [tool.name for tool in self.tool_registry.list_tools()]

        # If no specific allowed list, use all tools
        if allowed is None:
            allowed = all_tool_names

        # Apply permission mode filtering
        permission_mode = PermissionMode(self.config.agent.permission_mode)
        mode_allowed = get_allowed_tools_for_mode(permission_mode, allowed)

        # Build tool list
        tools = []
        for tool_name in mode_allowed:
            tool = self.tool_registry.get(tool_name)
            if tool:
                tools.append(tool.to_openai_tool_dict())

        return tools if tools else None

    async def run(self, prompt: str, job_type: str = "task") -> str:
        """Run agent with a prompt.

        Args:
            prompt: User prompt
            job_type: Type of job for tracking

        Returns:
            Final response
        """
        # Add user message
        await self._save_message(Message(role=Role.USER, content=prompt))

        # Create job
        job = Job(
            type=job_type,
            payload={"prompt": prompt, "agent_type": self.get_agent_type_name()},
        )
        await self.job_queue.push(job)
        await self.job_queue.update_status(job.id, JobStatus.IN_PROGRESS)

        # Run agent loop
        try:
            response = await self._agent_loop()
            await self.job_queue.update_status(
                job.id, JobStatus.COMPLETED, result={"response": response}
            )
            return response
        except Exception as e:
            await self.job_queue.update_status(
                job.id, JobStatus.FAILED, error=str(e)
            )
            raise

    async def _agent_loop(self) -> str:
        """Main agent loop with goal-based execution.

        Continues until task is complete (no more tool calls) or timeout/stop requested.

        Returns:
            Final response
        """
        # Initialize tracking
        start_time = time.time()
        timeout_seconds = getattr(self.config.agent, 'timeout_seconds', 1800)  # Default 30 min
        operation_count = 0
        warn_after = getattr(self.config.agent, 'warn_after_operations', 50)

        # Reset retry tracker for new task
        self.retry_tracker.reset()
        self.stop_requested = False

        while True:
            operation_count += 1

            # Check for timeout
            elapsed = time.time() - start_time
            if timeout_seconds and elapsed > timeout_seconds:
                console.print(f"[yellow]⏱️  Task timeout after {int(elapsed/60)} minutes[/yellow]\n")
                return f"Task timed out after {int(elapsed/60)} minutes. Progress may be incomplete."

            # Check if user requested stop
            if self.stop_requested:
                console.print("[yellow]⏸  Task stopped by user[/yellow]\n")
                return "Task stopped by user request."

            # Show soft warning after many operations
            if operation_count == warn_after:
                console.print(f"[yellow]⚠️  Still working after {warn_after} operations. This is taking longer than usual.[/yellow]")

            # Show progress
            elapsed_str = f"{int(elapsed/60)}m {int(elapsed%60)}s" if elapsed > 60 else f"{int(elapsed)}s"
            console.print(f"\n[dim]→ Working... ({elapsed_str} elapsed, {operation_count} operations)[/dim]")

            # Check if context compression is needed
            if self.context_manager.should_compress(self.messages):
                console.print("[dim]🗜️  Compressing context...[/dim]")
                self.messages = await self.message_compressor.compress(
                    self.messages,
                    keep_recent=10
                )

            # Get filtered tools
            tools = self._get_filtered_tools()

            # Generate response with streaming or normal mode
            if self.config.agent.streaming and not tools:
                # Streaming mode (only without tools)
                console.print("[dim]→ [/dim]", end="")

                content_chunks = []
                async for chunk in self.llm_client.generate_stream(
                    messages=self.messages,
                    tools=tools,
                ):
                    console.print(chunk, end="", style="")
                    content_chunks.append(chunk)

                console.print()  # Newline after streaming

                response = Message(
                    role=Role.ASSISTANT,
                    content="".join(content_chunks),
                    tool_calls=None,
                    thinking=None,
                )
            else:
                # Non-streaming mode
                with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
                    response = await self.llm_client.generate(
                        messages=self.messages,
                        tools=tools,
                    )

            # If in fallback mode, parse text for tool calls
            if self.config.agent.fallback_mode and self.fallback_parser:
                cleaned_content, tool_calls = self.fallback_parser.parse(response.content)
                response.content = cleaned_content
                if tool_calls:
                    response.tool_calls = tool_calls

            # Add assistant message
            await self._save_message(response)

            # Show thinking if available
            if response.thinking:
                if len(response.thinking) > 200:
                    console.print(f"[dim italic]💭 {response.thinking[:200]}...[/dim italic]\n")
                else:
                    console.print(f"[dim italic]💭 {response.thinking}[/dim italic]\n")

            # Check if there are tool calls
            if not response.tool_calls:
                # No more tool calls, task is complete!
                console.print("[dim]✓ Task complete[/dim]\n")
                stats = self.retry_tracker.get_stats()
                if stats["total_attempts"] > 0:
                    console.print(f"[dim]📊 Total operations: {stats['total_attempts']}[/dim]")
                return response.content

            # Execute tool calls with retry tracking
            await self._execute_tool_calls(response.tool_calls)

    async def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        """Execute tool calls and add results to messages.

        Args:
            tool_calls: List of tool calls to execute
        """
        # Show what tools are being called
        if len(tool_calls) == 1:
            tc = tool_calls[0]
            params_str = str(tc.parameters)
            if len(params_str) > 60:
                params_str = params_str[:60] + "..."
            console.print(f"[bold blue]🔧 Tool:[/bold blue] {tc.name}({params_str})")
        else:
            console.print(
                f"[bold blue]🔧 Tools:[/bold blue] {', '.join(tc.name for tc in tool_calls)} "
                f"[dim](parallel)[/dim]"
            )

        # Execute tools (parallel if configured)
        if self.config.agent.parallel_tool_calls and len(tool_calls) > 1:
            # Parallel execution
            import asyncio

            # Check if any tools are interactive (shouldn't be parallel, but handle gracefully)
            interactive_tools = {"AskUserQuestion"}
            has_interactive = any(tc.name in interactive_tools for tc in tool_calls)

            if has_interactive:
                # Execute without spinner if interactive tools are present
                results = await asyncio.gather(
                    *[
                        self.tool_registry.execute(tc.name, **tc.parameters)
                        for tc in tool_calls
                    ]
                )
            else:
                # Execute with spinner for non-interactive tools
                with console.status(
                    f"[bold green]Executing {len(tool_calls)} tools...[/bold green]",
                    spinner="dots"
                ):
                    results = await asyncio.gather(
                        *[
                            self.tool_registry.execute(tc.name, **tc.parameters)
                            for tc in tool_calls
                        ]
                    )
        else:
            # Sequential execution
            results = []
            for tc in tool_calls:
                # Check retry limit before executing
                should_execute, block_reason = self.retry_tracker.check_should_execute(
                    tc.name, tc.parameters
                )

                if not should_execute:
                    # Retry limit exceeded - create error result
                    from athena.models.tool import ToolResult
                    result = ToolResult(
                        success=False,
                        output="",
                        error=block_reason
                    )
                    results.append(result)
                    console.print(f"  [red]✗[/red] {tc.name}: {block_reason}")
                    continue

                # Skip spinner for interactive tools (they need clean console for user input)
                interactive_tools = {"AskUserQuestion"}

                if tc.name in interactive_tools:
                    # Execute without spinner for interactive tools
                    result = await self.tool_registry.execute(tc.name, **tc.parameters)
                    results.append(result)
                else:
                    # Execute with spinner for non-interactive tools
                    with console.status(
                        f"[bold green]Executing {tc.name}...[/bold green]",
                        spinner="dots"
                    ):
                        result = await self.tool_registry.execute(tc.name, **tc.parameters)
                        results.append(result)

                # Track success/failure for consecutive failure detection
                if result.success:
                    self.retry_tracker.record_success(tc.name, tc.parameters)
                else:
                    should_continue, stop_reason = self.retry_tracker.record_failure(
                        tc.name, tc.parameters
                    )
                    if not should_continue:
                        console.print(f"[red]🛑 {stop_reason}[/red]")
                        # Add the stop reason as an error message
                        self.stop_requested = True

                # Show result status
                if result.success:
                    output_preview = result.output[:100] + "..." if len(result.output) > 100 else result.output
                    console.print(f"  [green]✓[/green] {tc.name}: {output_preview}")
                else:
                    console.print(f"  [red]✗[/red] {tc.name}: {result.error}")

        # Add tool results to messages
        for tool_call, result in zip(tool_calls, results):
            # Format result content
            content = result.output
            if not result.success and result.error:
                content = f"Error: {result.error}\n{content}"

            # Create tool result message
            tool_result = Message(
                role=Role.TOOL,
                content=content,
                tool_call_id=tool_call.id,
                name=tool_call.name,
            )
            await self._save_message(tool_result)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation.

        Args:
            content: System message content
        """
        # Inject fallback instructions if in fallback mode
        if self.config.agent.fallback_mode and self.fallback_parser:
            content = self.fallback_parser.inject_instructions(content)

        # Insert at beginning if no system message exists
        if not self.messages or self.messages[0].role != Role.SYSTEM:
            self.messages.insert(0, Message(role=Role.SYSTEM, content=content))
        else:
            # Append to existing system message
            self.messages[0].content += f"\n\n{content}"

    def get_conversation_history(self) -> list[Message]:
        """Get the conversation history.

        Returns:
            List of messages
        """
        return self.messages

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
