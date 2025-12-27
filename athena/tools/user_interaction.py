"""User interaction tools."""

from typing import Any
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult

console = Console()


class AskUserQuestionTool(Tool):
    """Tool for asking the user questions during execution."""

    @property
    def name(self) -> str:
        return "AskUserQuestion"

    @property
    def description(self) -> str:
        return """Ask the user a question and wait for their response.

Use this when you need clarification, decisions, or additional information from the user.

Examples:
- "Which approach should I use: JWT or sessions?"
- "What should the API rate limit be?"
- "Should I create tests for this?"
- "Is this the correct file to modify?"

The user will see your question and provide an answer."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="question",
                type=ToolParameterType.STRING,
                description="The question to ask the user",
                required=True,
            ),
            ToolParameter(
                name="context",
                type=ToolParameterType.STRING,
                description="Optional context to help user understand the question",
                required=False,
            ),
        ]

    async def execute(
        self, question: str, context: str = None, **kwargs: Any
    ) -> ToolResult:
        """Execute user question."""
        try:
            # Format the question display
            display_text = question
            if context:
                display_text = f"{context}\n\n{question}"

            # Show question in a panel
            console.print()
            console.print(
                Panel(
                    display_text,
                    title="[bold yellow]Question from Athena[/bold yellow]",
                    border_style="yellow",
                )
            )

            # Get user response
            response = Prompt.ask("[bold green]Your answer[/bold green]")

            console.print()

            return ToolResult(
                success=True,
                output=f"User answered: {response}",
                metadata={"question": question, "answer": response},
            )

        except KeyboardInterrupt:
            return ToolResult(
                success=False,
                output="",
                error="User cancelled the question",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to get user input: {str(e)}",
            )
