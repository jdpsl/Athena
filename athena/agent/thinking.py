"""Thinking mode configuration."""

from enum import Enum


class ThinkingMode(str, Enum):
    """Thinking mode for agents."""

    DISABLED = "disabled"  # No thinking
    INTERLEAVED = "interleaved"  # Think between tool calls
    AUTO = "auto"  # Model decides when to think
