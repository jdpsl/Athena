"""File operation tools."""

import os
from pathlib import Path
from typing import Any, Optional
import aiofiles
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class ReadTool(Tool):
    """Tool for reading files."""

    @property
    def name(self) -> str:
        return "Read"

    @property
    def description(self) -> str:
        return "Reads a file from the filesystem. Returns content with line numbers."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Absolute path to the file to read",
                required=True,
            ),
            ToolParameter(
                name="offset",
                type=ToolParameterType.NUMBER,
                description="Line number to start reading from (optional)",
                required=False,
            ),
            ToolParameter(
                name="limit",
                type=ToolParameterType.NUMBER,
                description="Number of lines to read (optional)",
                required=False,
            ),
        ]

    async def execute(
        self,
        file_path: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute file read."""
        try:
            path = Path(file_path).expanduser().resolve()

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a file: {file_path}",
                )

            async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = await f.readlines()

            # Apply offset and limit
            start = (offset - 1) if offset else 0
            end = (start + limit) if limit else len(lines)
            lines = lines[start:end]

            # Format with line numbers (cat -n style)
            numbered_lines = [
                f"{i + start + 1:6d}\t{line.rstrip()}" for i, line in enumerate(lines)
            ]
            output = "\n".join(numbered_lines)

            return ToolResult(
                success=True,
                output=output,
                metadata={"line_count": len(lines), "file_path": str(path)},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read file: {str(e)}",
            )


class WriteTool(Tool):
    """Tool for writing files."""

    @property
    def name(self) -> str:
        return "Write"

    @property
    def description(self) -> str:
        return "Writes content to a file, creating or overwriting it."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Absolute path to the file to write",
                required=True,
            ),
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="Content to write to the file",
                required=True,
            ),
        ]

    async def execute(self, file_path: str, content: str, **kwargs: Any) -> ToolResult:
        """Execute file write."""
        try:
            path = Path(file_path).expanduser().resolve()

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)

            return ToolResult(
                success=True,
                output=f"File written successfully: {file_path}",
                metadata={"file_path": str(path), "bytes_written": len(content.encode())},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to write file: {str(e)}",
            )


class EditTool(Tool):
    """Tool for editing files with exact string replacement."""

    @property
    def name(self) -> str:
        return "Edit"

    @property
    def description(self) -> str:
        return "Performs exact string replacement in a file."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Absolute path to the file to edit",
                required=True,
            ),
            ToolParameter(
                name="old_string",
                type=ToolParameterType.STRING,
                description="Exact string to replace",
                required=True,
            ),
            ToolParameter(
                name="new_string",
                type=ToolParameterType.STRING,
                description="Replacement string",
                required=True,
            ),
            ToolParameter(
                name="replace_all",
                type=ToolParameterType.BOOLEAN,
                description="Replace all occurrences (default: false)",
                required=False,
                default=False,
            ),
        ]

    async def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute file edit."""
        try:
            path = Path(file_path).expanduser().resolve()

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                )

            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Check if old_string exists
            if old_string not in content:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String not found in file: {old_string[:100]}...",
                )

            # Check for multiple occurrences
            count = content.count(old_string)
            if count > 1 and not replace_all:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String appears {count} times. Use replace_all=true or provide more context.",
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(new_content)

            replacements = count if replace_all else 1
            return ToolResult(
                success=True,
                output=f"File edited successfully: {replacements} replacement(s) made",
                metadata={
                    "file_path": str(path),
                    "replacements": replacements,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to edit file: {str(e)}",
            )


class InsertTool(Tool):
    """Tool for inserting text at a specific line in a file."""

    @property
    def name(self) -> str:
        return "Insert"

    @property
    def description(self) -> str:
        return "Inserts text at a specific line number in a file. Line numbers are 1-indexed. Use 0 to insert at the beginning of the file."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Absolute path to the file to modify",
                required=True,
            ),
            ToolParameter(
                name="insert_line",
                type=ToolParameterType.NUMBER,
                description="Line number after which to insert text (0 for beginning of file, 1-indexed)",
                required=True,
            ),
            ToolParameter(
                name="new_text",
                type=ToolParameterType.STRING,
                description="Text to insert (will be added as new line(s))",
                required=True,
            ),
        ]

    async def execute(
        self,
        file_path: str,
        insert_line: int,
        new_text: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute text insertion at specified line."""
        try:
            path = Path(file_path).expanduser().resolve()

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                )

            # Read file
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                lines = await f.readlines()

            # Validate insert_line
            if insert_line < 0 or insert_line > len(lines):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid insert_line: {insert_line}. File has {len(lines)} lines.",
                )

            # Ensure new_text ends with newline if it doesn't already
            if new_text and not new_text.endswith('\n'):
                new_text += '\n'

            # Insert text at specified line
            if insert_line == 0:
                # Insert at beginning
                lines.insert(0, new_text)
            else:
                # Insert after the specified line (1-indexed)
                lines.insert(insert_line, new_text)

            # Write back to file
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.writelines(lines)

            return ToolResult(
                success=True,
                output=f"Text inserted successfully at line {insert_line}",
                metadata={
                    "file_path": str(path),
                    "insert_line": insert_line,
                    "lines_added": new_text.count('\n'),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to insert text: {str(e)}",
            )
