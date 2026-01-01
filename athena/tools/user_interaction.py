"""User interaction tools."""

from typing import Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult

console = Console()


class AskUserQuestionTool(Tool):
    """Tool for asking the user questions with optional multiple-choice options.

    Supports two formats:
    1. Simple text question (backward compatible)
    2. Multiple choice with 2-4 predefined options + automatic "Other" option
    """

    @property
    def name(self) -> str:
        return "AskUserQuestion"

    @property
    def description(self) -> str:
        return """Ask the user questions with optional multiple-choice options.

Use this when you need clarification, decisions, or additional information from the user.

Two formats supported:

1. Simple question (backward compatible):
   {"question": "What should the API rate limit be?"}

2. Multiple choice (1-4 questions, 2-4 options each):
   {
     "questions": [
       {
         "question": "Which database should we use?",
         "header": "DB Choice",
         "options": [
           {"label": "PostgreSQL", "description": "Powerful relational DB"},
           {"label": "MongoDB", "description": "NoSQL with flexible schema"}
         ],
         "multiSelect": false
       }
     ]
   }

Features:
- Users can select from predefined options OR choose "Other" to provide custom text
- Set multiSelect: true to allow selecting multiple options
- Header is a short label (max 12 chars) shown as a tag
- Each option should have a concise label (1-5 words) and helpful description"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            # Backward compatibility: simple question
            ToolParameter(
                name="question",
                type=ToolParameterType.STRING,
                description="Simple question text (backward compatible)",
                required=False,
            ),
            ToolParameter(
                name="context",
                type=ToolParameterType.STRING,
                description="Optional context for simple questions",
                required=False,
            ),
            # New format: multiple choice questions
            ToolParameter(
                name="questions",
                type=ToolParameterType.ARRAY,
                description="Array of 1-4 questions with multiple-choice options",
                required=False,
            ),
        ]

    async def execute(
        self,
        question: Optional[str] = None,
        context: Optional[str] = None,
        questions: Optional[list] = None,
        **kwargs: Any
    ) -> ToolResult:
        """Execute user question(s)."""
        try:
            # Determine which format is being used
            if questions:
                # New multiple-choice format
                return await self._execute_multiple_choice(questions)
            elif question:
                # Old simple format (backward compatible)
                return await self._execute_simple(question, context)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error="Must provide either 'question' or 'questions' parameter"
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

    async def _execute_simple(self, question: str, context: Optional[str]) -> ToolResult:
        """Execute simple text question (backward compatible)."""
        display_text = question
        if context:
            display_text = f"{context}\n\n{question}"

        console.print()
        console.print(
            Panel(
                display_text,
                title="[bold yellow]Question from Athena[/bold yellow]",
                border_style="yellow",
            )
        )

        response = Prompt.ask("[bold green]Your answer[/bold green]")
        console.print()

        return ToolResult(
            success=True,
            output=f"User answered: {response}",
            metadata={"question": question, "answer": response},
        )

    async def _execute_multiple_choice(self, questions: list) -> ToolResult:
        """Execute multiple-choice questions."""
        if not questions or len(questions) == 0:
            return ToolResult(
                success=False,
                output="",
                error="questions array cannot be empty"
            )

        if len(questions) > 4:
            return ToolResult(
                success=False,
                output="",
                error="Maximum 4 questions allowed per tool call"
            )

        all_answers = {}

        for q_data in questions:
            # Validate question format
            if "question" not in q_data:
                return ToolResult(
                    success=False,
                    output="",
                    error="Each question must have a 'question' field"
                )

            if "options" not in q_data:
                return ToolResult(
                    success=False,
                    output="",
                    error="Each question must have an 'options' array"
                )

            question_text = q_data["question"]
            header = q_data.get("header", "Question")[:12]  # Max 12 chars
            options = q_data["options"]
            multi_select = q_data.get("multiSelect", False)

            # Validate options
            if len(options) < 2 or len(options) > 4:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Each question must have 2-4 options (got {len(options)})"
                )

            # Display the question
            answer = await self._show_question_with_options(
                question_text,
                header,
                options,
                multi_select
            )

            all_answers[question_text] = answer

        # Format output
        output_lines = []
        for q, a in all_answers.items():
            if isinstance(a, list):
                output_lines.append(f"Q: {q}")
                output_lines.append(f"A: {', '.join(a)}")
            else:
                output_lines.append(f"Q: {q}")
                output_lines.append(f"A: {a}")

        return ToolResult(
            success=True,
            output="\n".join(output_lines),
            metadata={"answers": all_answers}
        )

    async def _show_question_with_options(
        self,
        question: str,
        header: str,
        options: list,
        multi_select: bool
    ) -> Any:
        """Display a question with multiple-choice options."""
        console.print()

        # Create header chip/tag
        header_text = Text(f" {header} ", style="bold white on blue")

        # Format options as simple text (no table for cleaner layout)
        options_text = []
        for i, opt in enumerate(options, 1):
            label = opt.get("label", f"Option {i}")
            description = opt.get("description", "")

            option_line = f"[cyan bold]{i}.[/cyan bold] [bold]{label}[/bold]"
            if description:
                # Align description under the label (calculate proper indentation)
                # "1. " = 3 chars + 1 for visual spacing = 4 total
                indent = len(str(i)) + 3  # number length + ". " + 1 extra space
                option_line += f"\n{' ' * indent}[dim]{description}[/dim]"

            options_text.append(option_line)

        # Add "Other" option
        other_num = len(options) + 1
        other_indent = len(str(other_num)) + 3
        options_text.append(
            f"[cyan bold]{other_num}.[/cyan bold] [bold]Other[/bold]\n{' ' * other_indent}[dim]Provide your own answer[/dim]"
        )

        # Build panel content
        panel_content = f"[bold]{question}[/bold]\n{header_text.markup}\n\n" + "\n\n".join(options_text)

        console.print(
            Panel(
                panel_content,
                title="[bold yellow]Question from Athena[/bold yellow]",
                border_style="yellow",
            )
        )

        if multi_select:
            console.print("[dim]You can select multiple options (comma-separated, e.g., '1,3') or type your own answer[/dim]")
            prompt_text = f"[bold green]Your choice(s)[/bold green] [dim](1-{len(options) + 1} or custom text)[/dim]"
        else:
            prompt_text = f"[bold green]Your choice[/bold green] [dim](1-{len(options) + 1} or custom text)[/dim]"

        response = Prompt.ask(prompt_text)

        # Parse response
        if multi_select and ',' in response:
            # Multiple selections
            selections = []
            for part in response.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(options):
                        selections.append(options[idx]["label"])
                    elif idx == len(options):
                        # "Other" selected along with other options
                        custom = Prompt.ask("[bold green]Please provide your answer[/bold green]")
                        selections.append(custom)
                else:
                    selections.append(part)
            console.print()
            return selections
        elif response.isdigit():
            # Single numeric selection
            idx = int(response) - 1
            if 0 <= idx < len(options):
                console.print()
                return options[idx]["label"]
            elif idx == len(options):
                # "Other" selected
                custom = Prompt.ask("[bold green]Please provide your answer[/bold green]")
                console.print()
                return custom
            else:
                console.print("[yellow]Invalid choice, using as custom answer[/yellow]")
                console.print()
                return response
        else:
            # Custom text answer
            console.print()
            return response
