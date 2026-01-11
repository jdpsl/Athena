"""Memory creation tool - allows agent to store user preferences."""

from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class MemoryCreateTool(Tool):
    """Create a new memory to remember user preferences across sessions.

    This tool allows the agent to proactively capture and store user preferences,
    system information, and patterns that should be remembered long-term.
    """

    def __init__(self, memory_manager=None):
        """Initialize with memory manager.

        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager

    @property
    def name(self) -> str:
        return "MemoryCreate"

    @property
    def description(self) -> str:
        return """Create a new memory to store user preferences across sessions.

IMPORTANT: Always ask the user for confirmation before creating a memory!

Use this tool when the user expresses preferences, constraints, or patterns that should be remembered:
- "Always use python3 instead of python"
- "I prefer pytest for testing"
- "Don't use pip3 without venv on this system"
- "I work with React and TypeScript"
- "Keep responses concise"

Detection patterns - look for phrases like:
- "always use...", "never use..."
- "I prefer...", "I like..."
- "use X instead of Y"
- "remember that...", "keep in mind..."
- "don't forget to..."

Workflow:
1. User says something like "always use python3 instead of python"
2. You detect this is a preference statement
3. ASK USER: "Should I remember this for future sessions?"
4. Wait for user confirmation (yes/no)
5. If confirmed, call this tool with the content

Memory will be automatically categorized by type:
- environment: System commands, tools (python3, brew, sudo)
- coding: Language/framework preferences (pytest, TypeScript, type hints)
- communication: Response style (concise, emoji, verbose)
- personal: Name, family, interests, background
- project: Project-specific patterns

Examples:
- content="Always use python3 instead of python"
  → Auto-detected as environment memory, visible to coding agents

- content="I prefer pytest and type hints"
  → Auto-detected as coding preference, visible to all agents

- content="My name is Sarah"
  → Auto-detected as personal, visible to planning/research agents

CRITICAL: Never create a memory without user confirmation!"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="The preference or information to remember",
                required=True,
            ),
            ToolParameter(
                name="reason",
                type=ToolParameterType.STRING,
                description="Brief explanation of why this should be remembered (helps user understand)",
                required=False,
            ),
        ]

    async def execute(self, content: str, reason: Optional[str] = None, **kwargs: Any) -> ToolResult:
        """Create a new memory after user confirmation.

        Args:
            content: The memory content to store
            reason: Optional explanation of why this is being remembered
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with created memory details
        """
        if not self.memory_manager:
            return ToolResult(
                success=False,
                output="",
                error="Memory manager not initialized",
            )

        if not content or not content.strip():
            return ToolResult(
                success=False,
                output="",
                error="Memory content cannot be empty",
            )

        try:
            # Create the memory (auto-detection of type and inject_for)
            memory = self.memory_manager.add_memory(
                content=content.strip(),
                source="explicit",  # User explicitly stated this
            )

            # Format success message
            output_lines = [
                f"✓ Memory created successfully!",
                f"",
                f"Content: {memory['content']}",
                f"Type: {memory['type']}",
                f"Visible to: {', '.join(memory['inject_for'])} agents",
                f"ID: {memory['id']}",
            ]

            if reason:
                output_lines.insert(2, f"Reason: {reason}")

            if memory.get('tags'):
                output_lines.append(f"Tags: {', '.join(memory['tags'])}")

            output = "\n".join(output_lines)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "memory_id": memory['id'],
                    "type": memory['type'],
                    "inject_for": memory['inject_for'],
                    "content": memory['content'],
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to create memory: {str(e)}",
            )
