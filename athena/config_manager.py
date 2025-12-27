"""Persistent configuration manager."""

import json
from pathlib import Path
from typing import Optional


class PersistentConfigManager:
    """Manages persistent configuration in ~/.athena/config.json"""

    def __init__(self):
        """Initialize config manager."""
        self.config_dir = Path.home() / ".athena"
        self.config_file = self.config_dir / "config.json"

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Optional[dict]:
        """Load configuration from ~/.athena/config.json

        Returns:
            Configuration dict or None if file doesn't exist
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_file}: {e}")
            return None

    def save(self, config: dict) -> bool:
        """Save configuration to ~/.athena/config.json

        Args:
            config: Configuration dict to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Failed to save config to {self.config_file}: {e}")
            return False

    def get_current_settings(
        self, model: str, api_base: str, api_key: str, temperature: float, mcp_servers: Optional[list] = None
    ) -> dict:
        """Get current settings as a dict.

        Args:
            model: Current model
            api_base: Current API base URL
            api_key: Current API key
            temperature: Current temperature
            mcp_servers: MCP server configurations

        Returns:
            Settings dict
        """
        settings = {
            "model": model,
            "api_base": api_base,
            "api_key": api_key,
            "temperature": temperature,
        }
        if mcp_servers is not None:
            settings["mcp_servers"] = mcp_servers
        return settings

    def apply_to_config(self, athena_config, settings: dict):
        """Apply saved settings to AthenaConfig.

        Args:
            athena_config: AthenaConfig object to update
            settings: Settings dict from saved config
        """
        if "model" in settings:
            athena_config.llm.model = settings["model"]
        if "api_base" in settings:
            athena_config.llm.api_base = settings["api_base"]
        if "api_key" in settings:
            athena_config.llm.api_key = settings["api_key"]
        if "temperature" in settings:
            athena_config.llm.temperature = settings["temperature"]
        if "mcp_servers" in settings:
            from athena.models.config import MCPServerConfig
            athena_config.mcp.servers = [MCPServerConfig(**server) for server in settings["mcp_servers"]]
            if athena_config.mcp.servers:
                athena_config.mcp.enabled = True
