"""Sub-agent implementation for specialized tasks."""

import uuid
from typing import Optional
from rich.console import Console
from athena.models.message import Message, Role
from athena.models.config import AthenaConfig
from athena.models.job import Job, JobStatus
from athena.llm.client import LLMClient
from athena.llm.thinking_injector import ThinkingInjector
from athena.tools.base import ToolRegistry
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.agent.types import AgentType, get_system_prompt

console = Console()


class SubAgent:
    """Sub-agent for handling specialized tasks."""

    def __init__(
        self,
        agent_type: AgentType,
        config: AthenaConfig,
        tool_registry: ToolRegistry,
        job_queue: SQLiteJobQueue,
        parent_job_id: Optional[str] = None,
    ):
        """Initialize sub-agent.

        Args:
            agent_type: Type of specialized agent
            config: Athena configuration
            tool_registry: Tool registry
            job_queue: Job queue
            parent_job_id: ID of parent job
        """
        self.agent_type = agent_type
        self.config = config
        self.tool_registry = tool_registry
        self.job_queue = job_queue
        self.parent_job_id = parent_job_id
        self.agent_id = str(uuid.uuid4())

        # Initialize LLM client
        thinking_injector = ThinkingInjector(
            enable_thinking=config.agent.enable_thinking,
            thinking_budget=config.agent.thinking_budget,
        )
        self.llm_client = LLMClient(config.llm, thinking_injector)

        # Conversation history
        self.messages: list[Message] = []

        # Add specialized system prompt
        system_prompt = get_system_prompt(agent_type)
        self.messages.append(Message(role=Role.SYSTEM, content=system_prompt))

    async def run(self, task_prompt: str, description: str = "") -> str:
        """Run the sub-agent with a task.

        Args:
            task_prompt: Task description
            description: Short description for job tracking

        Returns:
            Agent's final report
        """
        # Create job
        job = Job(
            type=f"sub_agent_{self.agent_type.value}",
            payload={"prompt": task_prompt, "description": description},
            parent_job_id=self.parent_job_id,
        )
        await self.job_queue.push(job)
        await self.job_queue.update_status(job.id, JobStatus.IN_PROGRESS)

        # Add user message
        self.messages.append(Message(role=Role.USER, content=task_prompt))

        # Run agent loop
        try:
            response = await self._agent_loop()
            await self.job_queue.update_status(
                job.id, JobStatus.COMPLETED, result={"response": response}
            )
            return response
        except Exception as e:
            await self.job_queue.update_status(job.id, JobStatus.FAILED, error=str(e))
            raise

    async def _agent_loop(self) -> str:
        """Sub-agent loop with tool execution.

        Returns:
            Final report
        """
        console.print(f"\n[bold magenta]🤖 Sub-Agent ({self.agent_type.value}) started[/bold magenta]")

        iteration = 0
        max_iterations = self.config.agent.max_iterations

        while iteration < max_iterations:
            iteration += 1

            console.print(f"[dim]  → Sub-agent iteration {iteration}/{max_iterations}[/dim]")

            # Generate response
            with console.status(f"[magenta]Sub-agent thinking...[/magenta]", spinner="dots"):
                response = await self.llm_client.generate(
                    messages=self.messages,
                    tools=self.tool_registry.to_openai_tools(),
                )

            # Add assistant message
            self.messages.append(response)

            # Check if there are tool calls
            if not response.tool_calls:
                # No more tool calls, return final response
                console.print(f"[bold magenta]✓ Sub-Agent ({self.agent_type.value}) completed[/bold magenta]\n")
                return response.content

            # Execute tool calls
            await self._execute_tool_calls(response.tool_calls)

        # Max iterations reached
        console.print(f"[yellow]⚠ Sub-agent max iterations reached[/yellow]\n")
        return "Maximum iterations reached. Task may be incomplete."

    async def _execute_tool_calls(self, tool_calls) -> None:
        """Execute tool calls and add results to messages.

        Args:
            tool_calls: List of tool calls to execute
        """
        # Show tools being called
        for tc in tool_calls:
            params_str = str(tc.parameters)
            if len(params_str) > 50:
                params_str = params_str[:50] + "..."
            console.print(f"  [magenta]🔧 Tool:[/magenta] {tc.name}({params_str})")

        # Execute tools (parallel if configured)
        if self.config.agent.parallel_tool_calls and len(tool_calls) > 1:
            import asyncio

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
                result = await self.tool_registry.execute(tc.name, **tc.parameters)
                results.append(result)

                # Show result
                if result.success:
                    preview = result.output[:80] + "..." if len(result.output) > 80 else result.output
                    console.print(f"    [green]✓[/green] {preview}")
                else:
                    console.print(f"    [red]✗[/red] {result.error}")

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

    def get_conversation_history(self) -> list[Message]:
        """Get the conversation history.

        Returns:
            List of messages
        """
        return self.messages
