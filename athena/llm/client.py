"""LLM client using OpenAI protocol."""

import json
from typing import Any, Optional
from openai import AsyncOpenAI
from athena.models.config import LLMConfig
from athena.models.message import Message, Role, ToolCall
from athena.llm.thinking_injector import ThinkingInjector


class LLMClient:
    """Client for interacting with OpenAI-compatible LLM APIs."""

    def __init__(
        self,
        config: LLMConfig,
        thinking_injector: Optional[ThinkingInjector] = None,
    ):
        """Initialize LLM client.

        Args:
            config: LLM configuration
            thinking_injector: Optional thinking injector
        """
        self.config = config
        self.thinking_injector = thinking_injector or ThinkingInjector()

        self.client = AsyncOpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
            timeout=config.timeout,
        )

    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Message:
        """Generate a completion.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens (overrides config)

        Returns:
            Generated message
        """
        # Convert messages to OpenAI format
        openai_messages = [msg.to_openai_dict() for msg in messages]

        # Inject thinking prompt if needed
        if self.thinking_injector.needs_injection(self.config.model):
            openai_messages = self.thinking_injector.inject_system_prompt(openai_messages)

        # Prepare request
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
        }

        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        elif self.config.max_tokens is not None:
            request_params["max_tokens"] = self.config.max_tokens

        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"

        # Make API call
        try:
            response = await self.client.chat.completions.create(**request_params)
        except Exception as e:
            # Enhanced error logging
            error_msg = f"LLM API Error: {str(e)}"
            if hasattr(e, 'response'):
                error_msg += f"\nStatus: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}"
                error_msg += f"\nResponse: {e.response.text[:500] if hasattr(e.response, 'text') else 'no response text'}"
            print(f"\n{'='*60}")
            print(f"ERROR: Failed to call LLM API")
            print(f"{'='*60}")
            print(f"API Base: {self.config.api_base}")
            print(f"Model: {self.config.model}")
            print(f"Error: {error_msg}")
            print(f"{'='*60}\n")
            raise

        # Parse response
        choice = response.choices[0]
        content = choice.message.content or ""

        # Extract thinking if injected
        thinking: Optional[str] = None
        if self.thinking_injector.needs_injection(self.config.model):
            thinking, content = self.thinking_injector.extract_thinking(content)

        # Parse tool calls
        tool_calls: Optional[list[ToolCall]] = None
        if choice.message.tool_calls:
            tool_calls = []
            for tc in choice.message.tool_calls:
                try:
                    # Parse arguments - handle both string and dict
                    args_str = tc.function.arguments
                    if isinstance(args_str, str):
                        parameters = json.loads(args_str) if args_str else {}
                    else:
                        parameters = args_str

                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            parameters=parameters,
                        )
                    )
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, store raw string
                    print(f"Warning: Failed to parse tool arguments: {e}")
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            parameters={"raw": args_str},
                        )
                    )

        return Message(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            thinking=thinking,
        )

    async def generate_stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Generate a streaming completion.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens (overrides config)

        Yields:
            Content chunks
        """
        # Convert messages to OpenAI format
        openai_messages = [msg.to_openai_dict() for msg in messages]

        # Inject thinking prompt if needed
        if self.thinking_injector.needs_injection(self.config.model):
            openai_messages = self.thinking_injector.inject_system_prompt(openai_messages)

        # Prepare request
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": temperature or self.config.temperature,
            "stream": True,
        }

        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        elif self.config.max_tokens is not None:
            request_params["max_tokens"] = self.config.max_tokens

        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"

        # Stream response
        try:
            stream = await self.client.chat.completions.create(**request_params)
        except Exception as e:
            # Enhanced error logging
            error_msg = f"LLM API Error: {str(e)}"
            if hasattr(e, 'response'):
                error_msg += f"\nStatus: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}"
                error_msg += f"\nResponse: {e.response.text[:500] if hasattr(e.response, 'text') else 'no response text'}"
            print(f"\n{'='*60}")
            print(f"ERROR: Failed to call LLM API (streaming)")
            print(f"{'='*60}")
            print(f"API Base: {self.config.api_base}")
            print(f"Model: {self.config.model}")
            print(f"Error: {error_msg}")
            print(f"{'='*60}\n")
            raise

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
