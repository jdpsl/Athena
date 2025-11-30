"""Text-based tool call parser for models without function calling support."""

import json
import re
from typing import Optional
from athena.models.message import ToolCall


class FallbackToolParser:
    """Parser for extracting tool calls from text output."""

    def __init__(self):
        """Initialize parser."""
        # Pattern: TOOL[ToolName]{json_args} or TOOL[ToolName]()
        self.pattern = re.compile(
            r'TOOL\[(\w+)\]\{([^}]*)\}|TOOL\[(\w+)\]\(\)',
            re.MULTILINE
        )

    def parse(self, text: str) -> tuple[str, list[ToolCall]]:
        """Parse tool calls from text.

        Args:
            text: Text containing potential tool calls

        Returns:
            Tuple of (cleaned_text, tool_calls)
        """
        tool_calls = []
        cleaned_text = text

        # Find all tool call matches
        matches = list(self.pattern.finditer(text))

        for i, match in enumerate(matches):
            # Extract tool name and arguments
            tool_name = match.group(1) or match.group(3)
            args_str = match.group(2) if match.group(2) else "{}"

            # Parse arguments
            try:
                # Try to parse as JSON
                if args_str.strip():
                    parameters = json.loads(f"{{{args_str}}}")
                else:
                    parameters = {}
            except json.JSONDecodeError:
                # If JSON fails, try to parse key: value format
                parameters = self._parse_key_value(args_str)

            # Create tool call
            tool_calls.append(
                ToolCall(
                    id=f"fallback_{i}",
                    name=tool_name,
                    parameters=parameters,
                )
            )

            # Remove tool call from text
            cleaned_text = cleaned_text.replace(match.group(0), "", 1)

        return cleaned_text.strip(), tool_calls

    def _parse_key_value(self, args_str: str) -> dict:
        """Parse key: value format arguments.

        Args:
            args_str: String like 'key1: "value1", key2: "value2"'

        Returns:
            Dictionary of parameters
        """
        parameters = {}

        # Split by commas (but not within quotes)
        parts = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str)

        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip().strip('"\'')
                value = value.strip().strip('"\'')

                # Try to convert to appropriate type
                if value.lower() == 'true':
                    parameters[key] = True
                elif value.lower() == 'false':
                    parameters[key] = False
                elif value.isdigit():
                    parameters[key] = int(value)
                elif self._is_float(value):
                    parameters[key] = float(value)
                else:
                    parameters[key] = value

        return parameters

    def _is_float(self, value: str) -> bool:
        """Check if string is a float."""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False

    def inject_instructions(self, system_prompt: str) -> str:
        """Add fallback tool calling instructions to system prompt.

        Args:
            system_prompt: Original system prompt

        Returns:
            Enhanced system prompt with fallback instructions
        """
        fallback_instructions = """

## IMPORTANT: Tool Calling Format

Since you don't have native function calling, use this text format to call tools:

TOOL[ToolName]{"param1": "value1", "param2": "value2"}

Examples:
- Read a file: TOOL[Read]{"file_path": "/path/to/file.py"}
- Write a file: TOOL[Write]{"file_path": "test.py", "content": "print('hello')"}
- Run bash: TOOL[Bash]{"command": "ls -la"}
- Search files: TOOL[Glob]{"pattern": "*.py"}
- Search content: TOOL[Grep]{"pattern": "def main", "path": "."}

Rules:
1. Each tool call must be on its own line
2. Use exact tool names (case-sensitive)
3. Use valid JSON for parameters (double quotes for strings)
4. Multiple tools: Put each on a separate line
5. After calling tools, wait for results before proceeding

Example multi-tool usage:
```
First, let me read the file:
TOOL[Read]{"file_path": "app.py"}

Then I'll check the git status:
TOOL[GitStatus]{}
```

The tool results will be provided back to you, then continue your response.
"""
        return system_prompt + fallback_instructions
