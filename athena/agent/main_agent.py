"""Main agent implementation."""

from typing import Optional
from athena.models.config import AthenaConfig
from athena.tools.base import ToolRegistry
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.context.manager import ContextManager
from athena.agent.base_agent import BaseAgent


class MainAgent(BaseAgent):
    """Main agent with full tool access."""

    def get_agent_type_name(self) -> str:
        """Get agent type name."""
        return "main"

    def get_allowed_tools(self) -> Optional[list[str]]:
        """Get allowed tools.

        Returns:
            None (all tools allowed)
        """
        return None  # All tools available
