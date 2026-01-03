"""Retry tracking to prevent infinite loops in agent execution."""

import hashlib
import json
from typing import Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class RetryTracker:
    """Tracks tool call retries to prevent infinite loops.

    Prevents scenarios like:
    - Same tool being called repeatedly with same parameters
    - Tool failing repeatedly without changing approach
    - Endless retry loops that waste tokens/time
    """

    def __init__(self, max_retries: int = 3, failure_limit: int = 5):
        """Initialize retry tracker.

        Args:
            max_retries: Maximum retries for same tool+params combination
            failure_limit: Maximum consecutive failures before stopping
        """
        self.max_retries = max_retries
        self.failure_limit = failure_limit

        # Track attempts by tool+params hash
        self.attempts: dict[str, int] = defaultdict(int)

        # Track consecutive failures
        self.consecutive_failures = 0

        # Track last N tool calls for pattern detection
        self.recent_calls: list[tuple[str, str]] = []  # [(tool_name, params_hash), ...]
        self.max_history = 10

    def _hash_params(self, params: dict[str, Any]) -> str:
        """Create stable hash of parameters.

        Args:
            params: Tool parameters

        Returns:
            Hash string
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()

    def _create_key(self, tool_name: str, params: dict[str, Any]) -> str:
        """Create unique key for tool+params combination.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Unique key
        """
        params_hash = self._hash_params(params)
        return f"{tool_name}:{params_hash}"

    def check_should_execute(
        self,
        tool_name: str,
        params: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Check if tool should be executed or has exceeded retry limit.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Tuple of (should_execute, reason_if_blocked)
        """
        key = self._create_key(tool_name, params)

        # Increment attempt counter
        self.attempts[key] += 1

        # Track in recent calls for pattern detection
        params_hash = self._hash_params(params)
        self.recent_calls.append((tool_name, params_hash))
        if len(self.recent_calls) > self.max_history:
            self.recent_calls.pop(0)

        # Check retry limit
        if self.attempts[key] > self.max_retries:
            return (
                False,
                f"Retry limit exceeded for {tool_name} with these parameters "
                f"({self.attempts[key]}/{self.max_retries} attempts). "
                f"Consider trying a different approach."
            )

        # Check for pattern: same tool called repeatedly in recent history
        if len(self.recent_calls) >= 5:
            recent_5 = self.recent_calls[-5:]
            if all(call[0] == tool_name and call[1] == params_hash for call in recent_5):
                return (
                    False,
                    f"{tool_name} called 5 times in a row with identical parameters. "
                    f"This appears to be stuck in a loop. Try a different approach."
                )

        return (True, None)

    def record_success(self, tool_name: str, params: dict[str, Any]):
        """Record successful tool execution.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
        """
        # Reset consecutive failure counter on success
        self.consecutive_failures = 0

    def record_failure(self, tool_name: str, params: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Record failed tool execution.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Tuple of (should_continue, reason_if_stopped)
        """
        self.consecutive_failures += 1

        # Check if we've hit the consecutive failure limit
        if self.consecutive_failures >= self.failure_limit:
            return (
                False,
                f"Stopped after {self.consecutive_failures} consecutive tool failures. "
                f"The task may not be achievable with current approach."
            )

        return (True, None)

    def reset(self):
        """Reset all tracking data."""
        self.attempts.clear()
        self.recent_calls.clear()
        self.consecutive_failures = 0

    def get_stats(self) -> dict[str, Any]:
        """Get current tracking statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_attempts": sum(self.attempts.values()),
            "unique_operations": len(self.attempts),
            "consecutive_failures": self.consecutive_failures,
            "most_retried": max(self.attempts.items(), key=lambda x: x[1]) if self.attempts else None,
        }
