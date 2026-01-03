"""Plan mode tools for entering and exiting planning phase."""

from typing import Any
from rich.console import Console
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult
from athena.models.config import AthenaConfig
from athena.models.permission import PermissionMode

console = Console()


class EnterPlanModeTool(Tool):
    """Tool for entering plan mode to explore and design before implementation."""

    def __init__(self, config: AthenaConfig):
        """Initialize enter plan mode tool.

        Args:
            config: Athena configuration
        """
        super().__init__()
        self.config = config

    @property
    def name(self) -> str:
        return "EnterPlanMode"

    @property
    def description(self) -> str:
        return """Enter plan mode to explore the codebase and design an implementation approach.

Use this tool proactively when you're about to start a non-trivial implementation task.
Getting user sign-off on your approach before writing code prevents wasted effort and
ensures alignment.

When to use:
- New feature implementation with multiple possible approaches
- Code modifications that affect existing behavior
- Architectural decisions needed (patterns, technologies, libraries)
- Multi-file changes (touching more than 2-3 files)
- Unclear requirements that need exploration first
- User preferences matter and could reasonably go multiple ways

What happens in plan mode:
1. You'll switch to read-only mode (no file modifications allowed)
2. You can explore the codebase using Read, Glob, Grep, Git, Web tools
3. You can use TodoWrite to plan implementation steps
4. You can use AskUserQuestion to clarify approaches
5. When ready, use ExitPlanMode to present your plan and begin implementation

DO NOT use for:
- Simple tasks (single-line fixes, typos, obvious bugs)
- Tasks where user gave very specific detailed instructions
- Pure research/exploration tasks"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute enter plan mode."""
        try:
            # Check if already in plan mode
            current_mode = PermissionMode(self.config.agent.permission_mode)
            if current_mode == PermissionMode.PLAN:
                return ToolResult(
                    success=True,
                    output="Already in plan mode. You can explore the codebase and design your approach.",
                    metadata={"already_in_plan_mode": True}
                )

            # Save previous mode so we can restore it later
            previous_mode = self.config.agent.permission_mode

            # Switch to plan mode
            self.config.agent.permission_mode = PermissionMode.PLAN.value

            console.print("\n[bold cyan]⏸ Entering Plan Mode[/bold cyan]")
            console.print("[dim]📖 Read-only mode activated. Explore the codebase and design your approach.[/dim]")
            console.print("[dim]Available tools: Read, Glob, Grep, ListDir, Git (read), Web, Math, TodoWrite, AskUserQuestion[/dim]")
            console.print("[dim]Use ExitPlanMode when ready to present your plan.[/dim]\n")

            return ToolResult(
                success=True,
                output=f"Entered plan mode (read-only). Previous mode was: {previous_mode}. "
                       f"You can now explore the codebase using read-only tools. "
                       f"Use ExitPlanMode when you're ready to present your implementation plan.",
                metadata={"previous_mode": previous_mode, "current_mode": "plan"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to enter plan mode: {str(e)}"
            )


class ExitPlanModeTool(Tool):
    """Tool for exiting plan mode after creating an implementation plan."""

    def __init__(self, config: AthenaConfig):
        """Initialize exit plan mode tool.

        Args:
            config: Athena configuration
        """
        super().__init__()
        self.config = config

    @property
    def name(self) -> str:
        return "ExitPlanMode"

    @property
    def description(self) -> str:
        return """Exit plan mode and return to normal mode to begin implementation.

Use this tool when you have:
1. Explored the codebase thoroughly
2. Designed your implementation approach
3. Created a plan using TodoWrite (if applicable)
4. Clarified any ambiguities with AskUserQuestion (if needed)
5. Are ready to present your plan and begin implementation

After exiting plan mode, you'll return to normal mode where you can write, edit, and execute code.

IMPORTANT: Before using this tool, ensure your plan is clear and unambiguous. If there are
multiple valid approaches or unclear requirements, use AskUserQuestion first to clarify with
the user."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute exit plan mode."""
        try:
            # Check if we're actually in plan mode
            current_mode = PermissionMode(self.config.agent.permission_mode)
            if current_mode != PermissionMode.PLAN:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Not currently in plan mode (current mode: {current_mode.display_name})"
                )

            # Return to normal mode (default)
            self.config.agent.permission_mode = PermissionMode.NORMAL.value

            console.print("\n[bold cyan]👤 Exiting Plan Mode[/bold cyan]")
            console.print("[dim]✓ Returning to Normal mode. You can now write code and execute operations.[/dim]\n")

            return ToolResult(
                success=True,
                output="Exited plan mode and returned to normal mode. You can now write code, edit files, "
                       "and execute operations. Present your implementation plan and proceed with the task.",
                metadata={"previous_mode": "plan", "current_mode": "normal"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to exit plan mode: {str(e)}"
            )
