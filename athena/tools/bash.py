"""Bash command execution tool."""

import asyncio
import os
from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class BashTool(Tool):
    """Tool for executing bash commands."""

    def __init__(self, timeout_ms: int = 120000):
        """Initialize bash tool.

        Args:
            timeout_ms: Default timeout in milliseconds
        """
        super().__init__()
        self.default_timeout_ms = timeout_ms
        self.working_dir = os.getcwd()

    @property
    def name(self) -> str:
        return "Bash"

    @property
    def description(self) -> str:
        return "Executes bash commands in a persistent shell session."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type=ToolParameterType.STRING,
                description="The bash command to execute",
                required=True,
            ),
            ToolParameter(
                name="description",
                type=ToolParameterType.STRING,
                description="Clear, concise description of what this command does",
                required=False,
            ),
            ToolParameter(
                name="timeout",
                type=ToolParameterType.NUMBER,
                description="Timeout in milliseconds (default: 120000, max: 600000)",
                required=False,
            ),
        ]

    async def execute(
        self,
        command: str,
        description: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute bash command."""
        try:
            # Determine timeout
            timeout_ms = timeout or self.default_timeout_ms
            timeout_ms = min(timeout_ms, 600000)  # Max 10 minutes
            timeout_s = timeout_ms / 1000

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_s
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout_s}s",
                )

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Combine output
            output = stdout_str
            if stderr_str:
                output += f"\n[stderr]\n{stderr_str}"

            # Truncate if too long (30000 chars like Claude Code)
            if len(output) > 30000:
                output = output[:30000] + "\n\n[Output truncated...]"

            success = process.returncode == 0

            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"Command exited with code {process.returncode}",
                metadata={
                    "return_code": process.returncode,
                    "description": description,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to execute command: {str(e)}",
            )

    def set_working_directory(self, path: str) -> None:
        """Set the working directory for commands.

        Args:
            path: New working directory
        """
        self.working_dir = path
