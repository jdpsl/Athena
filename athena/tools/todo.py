"""Todo management tool."""

import json
from typing import Any
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class TodoWriteTool(Tool):
    """Tool for managing todo lists."""

    def __init__(self):
        """Initialize todo tool."""
        super().__init__()
        self.todos: list[dict[str, str]] = []

    @property
    def name(self) -> str:
        return "TodoWrite"

    @property
    def description(self) -> str:
        return "Creates and updates a task list for tracking progress. Use for complex multi-step tasks."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="todos",
                type=ToolParameterType.ARRAY,
                description="Array of todo objects with content, activeForm, and status fields",
                required=True,
            ),
        ]

    async def execute(self, todos: list[dict[str, str]], **kwargs: Any) -> ToolResult:
        """Execute todo update."""
        try:
            # Validate todos
            for todo in todos:
                if "content" not in todo or "status" not in todo or "activeForm" not in todo:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Each todo must have 'content', 'status', and 'activeForm' fields",
                    )

                if todo["status"] not in ["pending", "in_progress", "completed"]:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Invalid status: {todo['status']}. Must be pending, in_progress, or completed",
                    )

            # Count in_progress todos
            in_progress_count = sum(1 for todo in todos if todo["status"] == "in_progress")
            if in_progress_count > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Only ONE todo should be in_progress at a time, found {in_progress_count}",
                )

            # Update todos
            self.todos = todos

            # Format output
            output_lines = ["Todo list updated:"]
            for i, todo in enumerate(todos, 1):
                status_icon = {
                    "pending": "[ ]",
                    "in_progress": "[→]",
                    "completed": "[✓]",
                }[todo["status"]]

                output_lines.append(f"{i}. {status_icon} {todo['content']}")

            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                metadata={"todo_count": len(todos)},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to update todos: {str(e)}",
            )

    def get_todos(self) -> list[dict[str, str]]:
        """Get current todos.

        Returns:
            List of todos
        """
        return self.todos

    def get_current_task(self) -> str | None:
        """Get the current in-progress task.

        Returns:
            Active form of current task or None
        """
        for todo in self.todos:
            if todo["status"] == "in_progress":
                return todo["activeForm"]
        return None
