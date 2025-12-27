"""Command loader for slash commands."""

from pathlib import Path
from typing import Optional


class CommandLoader:
    """Loads and manages slash commands from markdown files."""

    def __init__(self, commands_dir: str = ".athena/commands"):
        """Initialize command loader.

        Args:
            commands_dir: Directory containing command markdown files
        """
        self.commands_dir = Path(commands_dir)
        self.commands: dict[str, str] = {}

    def load_commands(self) -> None:
        """Load all commands from the commands directory."""
        if not self.commands_dir.exists():
            return

        for file_path in self.commands_dir.glob("*.md"):
            command_name = file_path.stem
            with open(file_path, "r", encoding="utf-8") as f:
                command_content = f.read()
            self.commands[command_name] = command_content

    def get_command(self, name: str) -> Optional[str]:
        """Get a command by name.

        Args:
            name: Command name (without leading slash)

        Returns:
            Command content or None
        """
        return self.commands.get(name)

    def list_commands(self) -> list[str]:
        """List all available commands.

        Returns:
            List of command names
        """
        return list(self.commands.keys())

    def expand_command(self, text: str) -> str:
        """Expand slash commands in text.

        Args:
            text: Input text potentially containing slash commands

        Returns:
            Text with slash commands expanded
        """
        if not text.startswith("/"):
            return text

        # Extract command name (first word after /)
        parts = text.split(maxsplit=1)
        command_name = parts[0][1:]  # Remove leading /
        args = parts[1] if len(parts) > 1 else ""

        # Get command content
        command_content = self.get_command(command_name)
        if not command_content:
            return text

        # Simple expansion: append args to command content
        if args:
            return f"{command_content}\n\nArguments: {args}"
        return command_content
