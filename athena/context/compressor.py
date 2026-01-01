"""Message compression for context management."""

from typing import Optional
from athena.models.message import Message, Role


class MessageCompressor:
    """Compresses old messages to preserve context window."""

    def __init__(self):
        """Initialize message compressor."""
        pass

    async def compress(
        self,
        messages: list[Message],
        keep_recent: int = 10,
        keep_system: bool = True,
    ) -> list[Message]:
        """Compress messages by summarizing old tool results.

        Strategy:
        1. Keep system message (if keep_system=True)
        2. Keep last N messages (keep_recent)
        3. Summarize everything in between

        Args:
            messages: Full message list
            keep_recent: Number of recent messages to preserve
            keep_system: Whether to keep system message

        Returns:
            Compressed message list
        """
        if len(messages) <= keep_recent + 1:
            # Not enough messages to compress
            return messages

        compressed = []

        # Keep system message
        if keep_system and messages and messages[0].role == Role.SYSTEM:
            compressed.append(messages[0])
            start_idx = 1
        else:
            start_idx = 0

        # Calculate split point
        split_point = len(messages) - keep_recent

        # Messages to compress
        to_compress = messages[start_idx:split_point]

        # Create summary
        summary = self._create_summary(to_compress)
        compressed.append(Message(
            role=Role.USER,
            content=f"[Previous conversation summary: {summary}]"
        ))

        # Keep recent messages
        compressed.extend(messages[split_point:])

        return compressed

    def _create_summary(self, messages: list[Message]) -> str:
        """Create summary of message sequence.

        Args:
            messages: Messages to summarize

        Returns:
            Summary text
        """
        tool_calls = []
        user_turns = 0

        for msg in messages:
            if msg.role == Role.USER:
                user_turns += 1
            elif msg.tool_calls:
                tool_calls.extend([tc.name for tc in msg.tool_calls])

        tool_summary = ", ".join(set(tool_calls)) if tool_calls else "none"

        return (
            f"{len(messages)} messages compressed, "
            f"{user_turns} user turns, "
            f"tools used: {tool_summary}"
        )
