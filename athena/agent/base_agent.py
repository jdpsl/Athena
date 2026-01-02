"""Base agent with shared functionality."""

import uuid
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

console = Console()


class BaseAgent(ABC):
    """Base agent with context management and execution loop."""

    def __init__(
        self,
        config: AthenaConfig,
        tool_registry: ToolRegistry,
        job_queue: SQLiteJobQueue,
        context_manager: Optional[ContextManager] = None,
    ):
        """Initialize base agent.

        Args:
            config: Athena configuration
            tool_registry: Tool registry
            job_queue: Job queue
            context_manager: Optional context manager (creates default if None)
        """
        self.config = config
        self.tool_registry = tool_registry
        self.job_queue = job_queue
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

    def _get_filtered_tools(self) -> Optional[list[dict]]:
        """Get filtered tools based on allowed_tools.

        Returns:
            List of tool definitions in OpenAI format, or None for all tools
        """
        # In fallback mode, don't send tools to API
        if self.config.agent.fallback_mode:
            return None

        allowed = self.get_allowed_tools()

        # None means all tools
        if allowed is None:
            return self.tool_registry.to_openai_tools()

        # Filter to only allowed tools
        tools = []
        for tool_name in allowed:
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
        self.messages.append(Message(role=Role.USER, content=prompt))

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
        """Main agent loop with context compression.

        Returns:
            Final response
        """
        iteration = 0
        max_iterations = self.config.agent.max_iterations

        while iteration < max_iterations:
            iteration += 1

            # Show iteration progress
            console.print(f"\n[dim]→ Iteration {iteration}/{max_iterations}[/dim]")

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
            self.messages.append(response)

            # Show thinking if available
            if response.thinking:
                if len(response.thinking) > 200:
                    console.print(f"[dim italic]💭 {response.thinking[:200]}...[/dim italic]\n")
                else:
                    console.print(f"[dim italic]💭 {response.thinking}[/dim italic]\n")

            # Check if there are tool calls
            if not response.tool_calls:
                # No more tool calls, return final response
                console.print("[dim]✓ Task complete[/dim]\n")
                return response.content

            # Execute tool calls
            await self._execute_tool_calls(response.tool_calls)

        # Max iterations reached
        console.print("[yellow]⚠ Maximum iterations reached[/yellow]\n")
        return "Maximum iterations reached. Task may be incomplete."

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
            self.messages.append(tool_result)

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
