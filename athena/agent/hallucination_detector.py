"""Hallucination detection agent - verifies claims match actions."""

from typing import Optional
from athena.models.message import Message, Role
from athena.models.config import AthenaConfig
from athena.llm.client import LLMClient


class HallucinationDetector:
    """Independent agent that detects when responses claim actions without performing them.

    This agent has NO context about the project - it only compares:
    1. What the assistant claimed to do
    2. What tools were actually called

    This prevents bias and focuses purely on detecting mismatches.
    """

    SYSTEM_PROMPT = """You are a hallucination detector for an AI coding assistant.

Your ONLY job is to detect when the assistant CLAIMS to have done something but DIDN'T actually call the tools to do it.

You will receive:
1. The assistant's response (what it said)
2. A list of tools that were actually called

Compare these and determine:
- Did the assistant claim to modify/create/update files?
- Did it actually call Edit/Write/Insert tools to do so?

IMPORTANT RULES:
- If the assistant says "I will..." or "Let me..." and then calls tools → NOT A HALLUCINATION
- If the assistant says "I've done X" but didn't call tools → HALLUCINATION
- If the assistant just explains or describes without claiming action → NOT A HALLUCINATION
- If the assistant called tools, it's not hallucinating (even if the description isn't perfect)

Output format:
HALLUCINATION: YES or NO
REASON: <one sentence explanation>

Examples:

Example 1:
Assistant: "I've updated the config.py file to add the new setting."
Tools called: []
Output:
HALLUCINATION: YES
REASON: Claimed to update file but didn't call Edit/Write tool.

Example 2:
Assistant: "Let me update the config file."
Tools called: [Edit(file_path="config.py", old_string="...", new_string="...")]
Output:
HALLUCINATION: NO
REASON: Actually called Edit tool to perform the action.

Example 3:
Assistant: "You should update the config file like this: <shows code>"
Tools called: []
Output:
HALLUCINATION: NO
REASON: Only explaining/suggesting, not claiming to have done it.

Example 4:
Assistant: "I updated the database schema and ran the migrations."
Tools called: [Edit(file_path="schema.sql", ...)]
Output:
HALLUCINATION: YES
REASON: Claimed to run migrations but only edited file, no Bash tool called.

Example 5:
Assistant: "Here's what I'll do: First, I'll update the file. <calls Edit tool> Done!"
Tools called: [Edit(...)]
Output:
HALLUCINATION: NO
REASON: Actually performed the action with Edit tool.

Be strict but fair. The goal is to catch cases where the assistant LIES about doing work.
"""

    def __init__(self, config: AthenaConfig):
        """Initialize hallucination detector.

        Args:
            config: Athena configuration (for LLM access)
        """
        self.config = config

        # Use fast, cheap model for detection (Haiku is perfect for this)
        detection_config = config.llm.copy()
        if config.llm.model_provider == "anthropic":
            detection_config.model_name = "claude-haiku-4"  # Fast and cheap

        self.llm_client = LLMClient(detection_config)

    async def detect(
        self,
        assistant_response: str,
        tools_called: list[str],
        tool_details: Optional[list[dict]] = None
    ) -> tuple[bool, str]:
        """Detect if the assistant hallucinated.

        Args:
            assistant_response: What the assistant said
            tools_called: List of tool names that were actually called
            tool_details: Optional detailed tool call info (name + parameters)

        Returns:
            Tuple of (is_hallucination, reason)
        """
        # Build the verification prompt
        tools_str = ", ".join(tools_called) if tools_called else "NONE"

        if tool_details:
            details_str = "\n".join([
                f"- {call['name']}({', '.join(f'{k}={v}' for k, v in call.get('parameters', {}).items())})"
                for call in tool_details
            ])
            tools_section = f"Tools called:\n{details_str}\n(Summary: {tools_str})"
        else:
            tools_section = f"Tools called: {tools_str}"

        prompt = f"""Assistant's response:
\"\"\"
{assistant_response}
\"\"\"

{tools_section}

Did the assistant hallucinate (claim to do something without calling tools)?
"""

        # Create messages for detection
        messages = [
            Message(role=Role.SYSTEM, content=self.SYSTEM_PROMPT),
            Message(role=Role.USER, content=prompt)
        ]

        # Get detection result
        response = await self.llm_client.generate(
            messages=messages,
            tools=None,  # No tools for detector
            temperature=0.0,  # Deterministic
        )

        # Parse response
        content = response.content.strip()

        # Extract HALLUCINATION: YES/NO
        is_hallucination = False
        reason = "Unknown"

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith("HALLUCINATION:"):
                answer = line.split(":", 1)[1].strip().upper()
                is_hallucination = answer == "YES"
            elif line.startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return is_hallucination, reason

    async def detect_batch(
        self,
        responses_and_tools: list[tuple[str, list[str]]]
    ) -> list[tuple[bool, str]]:
        """Detect hallucinations in batch for efficiency.

        Args:
            responses_and_tools: List of (response, tools_called) tuples

        Returns:
            List of (is_hallucination, reason) tuples
        """
        results = []
        for response, tools in responses_and_tools:
            result = await self.detect(response, tools)
            results.append(result)
        return results


class HallucinationStats:
    """Track hallucination detection statistics."""

    def __init__(self):
        self.total_checks = 0
        self.hallucinations_detected = 0
        self.hallucinations_prevented = 0
        self.false_positives = 0  # User can mark these
        self.examples = []  # Keep recent examples

    def record_check(self, is_hallucination: bool, response: str, reason: str):
        """Record a hallucination check.

        Args:
            is_hallucination: Whether hallucination was detected
            response: The assistant's response
            reason: Detection reason
        """
        self.total_checks += 1

        if is_hallucination:
            self.hallucinations_detected += 1

            # Keep recent examples (last 10)
            self.examples.append({
                "response": response[:200] + "..." if len(response) > 200 else response,
                "reason": reason,
            })
            if len(self.examples) > 10:
                self.examples.pop(0)

    def record_prevented(self):
        """Record that a hallucination was caught and prevented from reaching user."""
        self.hallucinations_prevented += 1

    def record_false_positive(self):
        """Record a false positive (user indicates it wasn't actually a hallucination)."""
        self.false_positives += 1
        if self.hallucinations_detected > 0:
            self.hallucinations_detected -= 1

    def get_stats(self) -> dict:
        """Get statistics.

        Returns:
            Dictionary of statistics
        """
        accuracy = 100.0
        if self.total_checks > 0:
            true_positives = self.hallucinations_detected - self.false_positives
            accuracy = ((self.total_checks - self.false_positives) / self.total_checks) * 100

        return {
            "total_checks": self.total_checks,
            "hallucinations_detected": self.hallucinations_detected,
            "hallucinations_prevented": self.hallucinations_prevented,
            "false_positives": self.false_positives,
            "detection_rate": f"{(self.hallucinations_detected / max(1, self.total_checks)) * 100:.1f}%",
            "accuracy": f"{accuracy:.1f}%",
            "recent_examples": self.examples,
        }

    def print_summary(self):
        """Print a summary of statistics."""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("HALLUCINATION DETECTION STATS")
        print("="*60)
        print(f"Total checks: {stats['total_checks']}")
        print(f"Hallucinations detected: {stats['hallucinations_detected']}")
        print(f"Hallucinations prevented: {stats['hallucinations_prevented']}")
        print(f"False positives: {stats['false_positives']}")
        print(f"Detection rate: {stats['detection_rate']}")
        print(f"Accuracy: {stats['accuracy']}")

        if stats['recent_examples']:
            print("\nRecent examples:")
            for i, ex in enumerate(stats['recent_examples'][-5:], 1):
                print(f"\n{i}. Response: {ex['response']}")
                print(f"   Reason: {ex['reason']}")

        print("="*60 + "\n")
