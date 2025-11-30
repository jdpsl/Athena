"""Task tool for spawning sub-agents."""

from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult
from athena.models.config import AthenaConfig
from athena.tools.base import ToolRegistry
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.agent.types import AgentType
from athena.agent.sub_agent import SubAgent


class TaskTool(Tool):
    """Tool for spawning specialized sub-agents."""

    def __init__(
        self,
        config: AthenaConfig,
        tool_registry: ToolRegistry,
        job_queue: SQLiteJobQueue,
        current_job_id: Optional[str] = None,
    ):
        """Initialize task tool.

        Args:
            config: Athena configuration
            tool_registry: Tool registry to pass to sub-agents
            job_queue: Job queue
            current_job_id: Current job ID (for parent tracking)
        """
        super().__init__()
        self.config = config
        self.tool_registry = tool_registry
        self.job_queue = job_queue
        self.current_job_id = current_job_id

    @property
    def name(self) -> str:
        return "Task"

    @property
    def description(self) -> str:
        return """Launch a specialized agent to handle complex, multi-step tasks autonomously.

The agent will work independently and return a final report. Use this when:
- Task requires multiple steps and exploration
- You need specialized expertise (code review, testing, planning)
- Complex codebase navigation is needed

The sub-agent has access to the same tools and will work autonomously."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="subagent_type",
                type=ToolParameterType.STRING,
                description="Type of specialized agent to use",
                required=True,
                enum=[
                    "general-purpose",
                    "Explore",
                    "Plan",
                    "code-reviewer",
                    "test-runner",
                ],
            ),
            ToolParameter(
                name="prompt",
                type=ToolParameterType.STRING,
                description="Detailed task for the agent to perform autonomously",
                required=True,
            ),
            ToolParameter(
                name="description",
                type=ToolParameterType.STRING,
                description="Short 3-5 word description of the task",
                required=True,
            ),
        ]

    async def execute(
        self,
        subagent_type: str,
        prompt: str,
        description: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute task by spawning a sub-agent."""
        try:
            # Validate agent type
            try:
                agent_type = AgentType(subagent_type)
            except ValueError:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid agent type: {subagent_type}. Must be one of: {[t.value for t in AgentType]}",
                )

            # Create sub-agent
            sub_agent = SubAgent(
                agent_type=agent_type,
                config=self.config,
                tool_registry=self.tool_registry,
                job_queue=self.job_queue,
                parent_job_id=self.current_job_id,
            )

            # Run sub-agent
            result = await sub_agent.run(prompt, description)

            # Format output
            output = f"""Sub-Agent Report ({agent_type.value})
Task: {description}

{result}

---
Sub-agent completed task successfully."""

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "agent_type": agent_type.value,
                    "description": description,
                    "agent_id": sub_agent.agent_id,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Sub-agent execution failed: {str(e)}",
            )
