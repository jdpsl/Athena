"""Configuration models."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration."""

    api_base: str = Field(
        default="http://localhost:1234/v1",
        description="OpenAI-compatible API base URL",
    )
    api_key: str = Field(default="not-needed-for-local", description="API key")
    model: str = Field(default="local-model", description="Model name")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens to generate")
    timeout: int = Field(default=120, description="Request timeout in seconds")


class AgentConfig(BaseModel):
    """Agent configuration."""

    max_iterations: int = Field(default=50, description="Max agent iterations")
    enable_thinking: bool = Field(default=True, description="Enable thinking tag injection")
    thinking_budget: int = Field(
        default=32000, description="Max tokens for thinking content"
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Allow parallel tool execution"
    )
    fallback_mode: bool = Field(
        default=False, description="Use text-based tool calling for models without function calling"
    )
    streaming: bool = Field(
        default=False, description="Enable streaming responses (show output as generated)"
    )

    # Context compression settings
    context_max_tokens: int = Field(
        default=8000, description="Maximum tokens before compression is triggered"
    )
    context_compression_threshold: float = Field(
        default=0.75, description="Compress when context reaches this % of max_tokens (0.0-1.0)"
    )

    # Cautious/Collaborative mode settings
    interaction_mode: str = Field(
        default="collaborative", description="Agent interaction style: 'collaborative' or 'autonomous'"
    )
    ask_before_execution: bool = Field(
        default=True, description="Ask clarifying questions before executing tasks"
    )
    ask_before_multi_file_changes: bool = Field(
        default=True, description="Ask confirmation before changing multiple files"
    )
    require_plan_approval: bool = Field(
        default=True, description="Require user approval for implementation plans on complex tasks"
    )


class ToolsConfig(BaseModel):
    """Tools configuration."""

    bash_timeout: int = Field(default=120000, description="Bash timeout in milliseconds")
    max_file_size: int = Field(default=10000000, description="Max file size in bytes")
    max_search_results: int = Field(default=100, description="Max search results")
    sandbox_enabled: bool = Field(default=False, description="Enable sandboxed execution")

    # Web search configuration
    search_api: str = Field(default="duckduckgo", description="Search API to use (duckduckgo, brave, google, searxng)")
    brave_api_key: Optional[str] = Field(default=None, description="Brave Search API key")
    google_api_key: Optional[str] = Field(default=None, description="Google Custom Search API key")
    google_cx: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    searxng_url: Optional[str] = Field(default=None, description="SearXNG instance URL")


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str = Field(description="Server identifier (e.g., 'postgres', 'filesystem')")
    transport: Literal["stdio", "http"] = Field(description="Connection transport type")

    # Stdio transport fields
    command: Optional[str] = Field(default=None, description="Command to launch server (stdio)")
    args: Optional[list[str]] = Field(default_factory=list, description="Command arguments (stdio)")
    env: Optional[dict[str, str]] = Field(default_factory=dict, description="Environment variables (stdio)")

    # HTTP transport fields
    url: Optional[str] = Field(default=None, description="Server URL (http)")

    # Common fields
    enabled: bool = Field(default=True, description="Enable this server")
    timeout: int = Field(default=30, description="Connection timeout in seconds")


class MCPConfig(BaseModel):
    """MCP client configuration."""

    enabled: bool = Field(default=False, description="Enable MCP support")
    servers: list[MCPServerConfig] = Field(default_factory=list, description="MCP servers to connect to")


class AthenaConfig(BaseModel):
    """Main Athena configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    agent: AgentConfig = Field(default_factory=AgentConfig, description="Agent configuration")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="Tools configuration")
    mcp: MCPConfig = Field(default_factory=MCPConfig, description="MCP configuration")
    working_directory: str = Field(default=".", description="Working directory")
    debug: bool = Field(default=False, description="Enable debug mode")

    @classmethod
    def from_yaml(cls, path: str) -> "AthenaConfig":
        """Load configuration from YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> "AthenaConfig":
        """Load configuration from environment variables."""
        from dotenv import load_dotenv
        import os

        load_dotenv()

        return cls(
            llm=LLMConfig(
                api_base=os.getenv("ATHENA_API_BASE", "http://localhost:1234/v1"),
                api_key=os.getenv("ATHENA_API_KEY", "not-needed-for-local"),
                model=os.getenv("ATHENA_MODEL", "local-model"),
                temperature=float(os.getenv("ATHENA_TEMPERATURE", "0.7")),
            ),
            agent=AgentConfig(
                max_iterations=int(os.getenv("ATHENA_MAX_ITERATIONS", "50")),
                enable_thinking=os.getenv("ATHENA_ENABLE_THINKING", "true").lower()
                == "true",
            ),
            working_directory=os.getenv("ATHENA_WORKING_DIR", "."),
            debug=os.getenv("ATHENA_DEBUG", "false").lower() == "true",
        )
