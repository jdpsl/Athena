"""Context window manager."""

from typing import Optional
from athena.models.message import Message


class ContextManager:
    """Manages context window size and compression triggers."""

    def __init__(
        self,
        max_tokens: int = 8000,
        compression_threshold: float = 0.75,
    ):
        """Initialize context manager.

        Args:
            max_tokens: Maximum tokens to allow in context
            compression_threshold: Compress when this % of max is reached
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold

    def estimate_tokens(self, messages: list[Message]) -> int:
        """Estimate token count for messages.

        Uses rough heuristic: 1 token ≈ 4 characters

        Args:
            messages: List of messages

        Returns:
            Estimated token count
        """
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.content or "")
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total_chars += len(str(tc.parameters))

        return total_chars // 4  # Rough estimate

    def should_compress(self, messages: list[Message]) -> bool:
        """Check if messages should be compressed.

        Args:
            messages: List of messages

        Returns:
            True if compression is needed
        """
        estimated_tokens = self.estimate_tokens(messages)
        threshold = self.max_tokens * self.compression_threshold
        return estimated_tokens > threshold

    def get_compression_stats(self, messages: list[Message]) -> dict:
        """Get compression statistics.

        Args:
            messages: List of messages

        Returns:
            Dict with token stats
        """
        tokens = self.estimate_tokens(messages)
        return {
            "current_tokens": tokens,
            "max_tokens": self.max_tokens,
            "utilization": tokens / self.max_tokens,
            "should_compress": self.should_compress(messages),
        }
