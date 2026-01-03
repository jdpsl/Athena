"""Permission mode definitions."""

from enum import Enum


class PermissionMode(str, Enum):
    """Permission modes for controlling agent behavior.

    Similar to Claude Code's permission modes for safety and control.
    """

    NORMAL = "normal"
    """Normal mode - ask before executing operations (default)"""

    AUTO_ACCEPT = "auto-accept"
    """Auto-accept mode - execute operations without asking"""

    PLAN = "plan"
    """Plan mode - read-only operations, no file modifications"""

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get display-friendly name."""
        if self == PermissionMode.NORMAL:
            return "Normal (ask before acting)"
        elif self == PermissionMode.AUTO_ACCEPT:
            return "Auto-Accept (execute directly)"
        elif self == PermissionMode.PLAN:
            return "Plan (read-only)"
        return self.value

    @property
    def icon(self) -> str:
        """Get mode icon."""
        if self == PermissionMode.NORMAL:
            return "👤"
        elif self == PermissionMode.AUTO_ACCEPT:
            return "⚡"
        elif self == PermissionMode.PLAN:
            return "⏸"
        return ""

    def allows_writes(self) -> bool:
        """Check if this mode allows write operations."""
        return self != PermissionMode.PLAN

    def requires_approval(self) -> bool:
        """Check if this mode requires user approval."""
        return self == PermissionMode.NORMAL

    @classmethod
    def next_mode(cls, current: "PermissionMode") -> "PermissionMode":
        """Get next mode in cycle (for keyboard shortcut).

        Cycle: Normal → Auto-Accept → Plan → Normal

        Args:
            current: Current permission mode

        Returns:
            Next permission mode in cycle
        """
        modes = [cls.NORMAL, cls.AUTO_ACCEPT, cls.PLAN]
        current_idx = modes.index(current)
        next_idx = (current_idx + 1) % len(modes)
        return modes[next_idx]


# Read-only tools (allowed in Plan mode)
READ_ONLY_TOOLS = {
    "Read",
    "Glob",
    "Grep",
    "ListDir",
    "GitStatus",
    "GitDiff",
    "GitLog",
    "WebSearch",
    "WebFetch",
    "NotebookRead",
    "TodoWrite",  # Planning tool
    "AskUserQuestion",
    "Math",
}

# Write/modification tools (blocked in Plan mode)
WRITE_TOOLS = {
    "Write",
    "Edit",
    "Insert",
    "DeleteFile",
    "MoveFile",
    "CopyFile",
    "MakeDir",
    "Bash",
    "GitCommit",
    "GitPush",
    "GitBranch",
    "GitCreatePR",
    "NotebookEdit",
    "NotebookExecute",
    "NotebookCreate",
}


def get_allowed_tools_for_mode(
    mode: PermissionMode,
    all_tools: list[str]
) -> list[str]:
    """Get list of allowed tools for a permission mode.

    Args:
        mode: Permission mode
        all_tools: List of all available tool names

    Returns:
        List of allowed tool names for this mode
    """
    if mode == PermissionMode.PLAN:
        # Only allow read-only tools in plan mode
        return [tool for tool in all_tools if tool in READ_ONLY_TOOLS]
    else:
        # Normal and auto-accept allow all tools
        return all_tools
