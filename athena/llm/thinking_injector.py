"""Thinking tag injection for models without native support."""

import re
from typing import Optional


class ThinkingInjector:
    """Injects and parses thinking tags for models that don't support them natively."""

    THINKING_SYSTEM_PROMPT = """You have access to internal reasoning capabilities using thinking tags. When solving complex problems:

1. Use <thinking> tags to show your internal reasoning process
2. Think through the problem step by step
3. Consider multiple approaches
4. Analyze potential issues
5. Plan your actions before executing

Example:
<thinking>
The user wants to add authentication. I need to:
1. Check if there's existing auth code
2. Determine the auth method (JWT vs sessions)
3. Find where to implement it
Let me start by searching for existing auth patterns.
</thinking>

Then I'll search the codebase for authentication patterns.

Your thinking should be detailed and thorough, but the user will not see it. After your thinking, provide your response and any tool calls."""

    MODELS_WITH_NATIVE_THINKING = {
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3-5-sonnet",
        "deepseek-chat",
        "deepseek-r1",
    }

    def __init__(self, enable_thinking: bool = True, thinking_budget: int = 32000):
        """Initialize thinking injector.

        Args:
            enable_thinking: Whether to enable thinking injection
            thinking_budget: Maximum tokens for thinking content
        """
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

    def needs_injection(self, model_name: str) -> bool:
        """Check if a model needs thinking injection.

        Args:
            model_name: Name of the model

        Returns:
            True if thinking should be injected
        """
        if not self.enable_thinking:
            return False

        # Check if model has native thinking support
        for native_model in self.MODELS_WITH_NATIVE_THINKING:
            if native_model in model_name.lower():
                return False

        return True

    def inject_system_prompt(self, messages: list[dict]) -> list[dict]:
        """Inject thinking system prompt into messages.

        Args:
            messages: List of message dicts

        Returns:
            Modified messages with thinking prompt injected
        """
        if not messages:
            return [{"role": "system", "content": self.THINKING_SYSTEM_PROMPT}]

        # If first message is system, append to it
        if messages[0]["role"] == "system":
            messages[0]["content"] = f"{messages[0]['content']}\n\n{self.THINKING_SYSTEM_PROMPT}"
        else:
            # Insert at beginning
            messages.insert(0, {"role": "system", "content": self.THINKING_SYSTEM_PROMPT})

        return messages

    def extract_thinking(self, content: str) -> tuple[Optional[str], str]:
        """Extract thinking content from response.

        Args:
            content: Response content

        Returns:
            Tuple of (thinking_content, remaining_content)
        """
        # Match <thinking>...</thinking> tags
        pattern = r"<thinking>(.*?)</thinking>"
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            return None, content

        # Combine all thinking blocks
        thinking = "\n\n".join(match.strip() for match in matches)

        # Remove thinking tags from content
        remaining = re.sub(pattern, "", content, flags=re.DOTALL).strip()

        # Enforce thinking budget (rough token estimate: 1 token ~= 4 chars)
        max_chars = self.thinking_budget * 4
        if len(thinking) > max_chars:
            thinking = thinking[:max_chars] + "\n\n[Thinking truncated due to length...]"

        return thinking, remaining

    def format_for_display(self, thinking: Optional[str], content: str) -> str:
        """Format thinking and content for display.

        Args:
            thinking: Thinking content (or None)
            content: Main content

        Returns:
            Formatted string
        """
        if not thinking:
            return content

        return f"[Internal Reasoning]\n{thinking}\n\n[Response]\n{content}"
