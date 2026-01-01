"""Specialized agent implementations."""

from typing import Optional
from athena.agent.base_agent import BaseAgent


class ExploreAgent(BaseAgent):
    """Fast exploration agent - search and read only."""

    def get_agent_type_name(self) -> str:
        return "explore"

    def get_allowed_tools(self) -> Optional[list[str]]:
        """Only search and read tools.

        Returns:
            List of allowed tools: Glob, Grep, Read
        """
        return ["Glob", "Grep", "Read"]


class PlanAgent(BaseAgent):
    """Planning agent - search, read, and planning tools."""

    def get_agent_type_name(self) -> str:
        return "plan"

    def get_allowed_tools(self) -> Optional[list[str]]:
        """Search, read, and planning tools.

        Returns:
            List of allowed tools: Glob, Grep, Read, TodoWrite
        """
        return ["Glob", "Grep", "Read", "TodoWrite"]


class CodeReviewAgent(BaseAgent):
    """Code review agent - read and search only."""

    def get_agent_type_name(self) -> str:
        return "code-reviewer"

    def get_allowed_tools(self) -> Optional[list[str]]:
        """Read and search tools.

        Returns:
            List of allowed tools: Read, Grep, Glob, TodoWrite
        """
        return ["Read", "Grep", "Glob", "TodoWrite"]


class TestRunnerAgent(BaseAgent):
    """Test runner agent - read and execute."""

    def get_agent_type_name(self) -> str:
        return "test-runner"

    def get_allowed_tools(self) -> Optional[list[str]]:
        """Read, search, and execution tools.

        Returns:
            List of allowed tools: Read, Grep, Glob, Bash
        """
        return ["Read", "Grep", "Glob", "Bash"]
