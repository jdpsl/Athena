"""Message models for agent communication."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Represents a tool call made by the agent."""

    id: str = Field(description="Unique identifier for this tool call")
    name: str = Field(description="Name of the tool to call")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ToolResult(BaseModel):
    """Result from a tool execution."""

    tool_call_id: str = Field(description="ID of the tool call this is responding to")
    tool_name: str = Field(description="Name of the tool that was executed")
    content: str = Field(description="Result content")
    success: bool = Field(default=True, description="Whether execution succeeded")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class Message(BaseModel):
    """A message in the conversation."""

    role: Role = Field(description="Message role")
    content: str = Field(description="Message content")
    tool_calls: Optional[list[ToolCall]] = Field(
        default=None, description="Tool calls made in this message"
    )
    tool_call_id: Optional[str] = Field(
        default=None, description="Tool call ID if this is a tool response"
    )
    name: Optional[str] = Field(
        default=None, description="Tool name if this is a tool response"
    )
    thinking: Optional[str] = Field(
        default=None, description="Internal reasoning/thinking content"
    )

    def to_openai_dict(self) -> dict[str, Any]:
        """Convert to OpenAI API format."""
        msg: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": str(tc.parameters),
                    },
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.name:
            msg["name"] = self.name

        return msg
