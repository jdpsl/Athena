"""Configuration models."""

from typing import Optional
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


class AthenaConfig(BaseModel):
    """Main Athena configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    agent: AgentConfig = Field(default_factory=AgentConfig, description="Agent configuration")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="Tools configuration")
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
