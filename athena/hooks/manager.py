"""Hook manager for event-driven control."""

from enum import Enum
from typing import Any, Callable, Optional
import asyncio


class HookType(str, Enum):
    """Types of hooks."""

    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    USER_PROMPT_SUBMIT = "user_prompt_submit"
    STOP = "stop"


class HookManager:
    """Manages hooks for event-driven control."""

    def __init__(self):
        """Initialize hook manager."""
        self.hooks: dict[HookType, list[Callable]] = {
            HookType.PRE_TOOL_USE: [],
            HookType.POST_TOOL_USE: [],
            HookType.USER_PROMPT_SUBMIT: [],
            HookType.STOP: [],
        }

    def register(self, hook_type: HookType, callback: Callable) -> None:
        """Register a hook callback.

        Args:
            hook_type: Type of hook
            callback: Callback function (can be sync or async)
        """
        self.hooks[hook_type].append(callback)

    async def trigger(self, hook_type: HookType, context: dict[str, Any]) -> dict[str, Any]:
        """Trigger a hook.

        Args:
            hook_type: Type of hook to trigger
            context: Context data for the hook

        Returns:
            Modified context after all hooks execute
        """
        for callback in self.hooks[hook_type]:
            # Support both sync and async callbacks
            if asyncio.iscoroutinefunction(callback):
                result = await callback(context)
            else:
                result = callback(context)

            # If callback returns modified context, use it
            if result is not None:
                context = result

        return context

    def clear(self, hook_type: Optional[HookType] = None) -> None:
        """Clear hooks.

        Args:
            hook_type: Specific hook type to clear, or None to clear all
        """
        if hook_type:
            self.hooks[hook_type] = []
        else:
            for ht in HookType:
                self.hooks[ht] = []
