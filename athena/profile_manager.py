"""Profile manager for saving and loading configuration profiles."""

import json
from pathlib import Path
from typing import Optional
from athena.models.config import AthenaConfig


class ProfileManager:
    """Manages configuration profiles."""

    def __init__(self, profiles_dir: str = None):
        """Initialize profile manager.

        Args:
            profiles_dir: Directory to store profiles (default: ~/.athena/profiles)
        """
        if profiles_dir:
            self.profiles_dir = Path(profiles_dir)
        else:
            self.profiles_dir = Path.home() / ".athena" / "profiles"

        # Create directory if it doesn't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Track current profile
        self.current_profile: Optional[str] = None
        self._load_current_profile()

    def _load_current_profile(self) -> None:
        """Load the currently active profile name."""
        current_file = self.profiles_dir / ".current"
        if current_file.exists():
            self.current_profile = current_file.read_text().strip()

    def _save_current_profile(self, name: Optional[str]) -> None:
        """Save the currently active profile name.

        Args:
            name: Profile name or None for default
        """
        current_file = self.profiles_dir / ".current"
        if name:
            current_file.write_text(name)
            self.current_profile = name
        else:
            if current_file.exists():
                current_file.unlink()
            self.current_profile = None

    def save_profile(self, config: AthenaConfig, name: Optional[str] = None) -> str:
        """Save current configuration as a profile.

        Args:
            config: Configuration to save
            name: Profile name (None = save to current/default)

        Returns:
            Name of saved profile
        """
        # Determine profile name
        if name is None:
            # Save to current profile or "default"
            name = self.current_profile or "default"

        # Build profile data
        profile_data = {
            "name": name,
            "llm": {
                "api_base": config.llm.api_base,
                "api_key": config.llm.api_key,
                "model": config.llm.model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "timeout": config.llm.timeout,
            },
            "agent": {
                "timeout_seconds": config.agent.timeout_seconds,
                "max_retries": config.agent.max_retries,
                "failure_limit": config.agent.failure_limit,
                "enable_thinking": config.agent.enable_thinking,
                "thinking_budget": config.agent.thinking_budget,
                "parallel_tool_calls": config.agent.parallel_tool_calls,
                "fallback_mode": config.agent.fallback_mode,
                "streaming": config.agent.streaming,
                "permission_mode": config.agent.permission_mode,
            },
        }

        # Save to file
        profile_file = self.profiles_dir / f"{name}.json"
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)

        # Update current profile
        self._save_current_profile(name)

        return name

    def load_profile(self, name: str) -> Optional[dict]:
        """Load a profile by name.

        Args:
            name: Profile name

        Returns:
            Profile data dict or None if not found
        """
        profile_file = self.profiles_dir / f"{name}.json"

        if not profile_file.exists():
            return None

        with open(profile_file, 'r') as f:
            profile_data = json.load(f)

        # Update current profile
        self._save_current_profile(name)

        return profile_data

    def apply_profile(self, config: AthenaConfig, profile_data: dict) -> None:
        """Apply profile data to configuration.

        Args:
            config: Configuration to update
            profile_data: Profile data to apply
        """
        # Apply LLM settings
        if "llm" in profile_data:
            llm = profile_data["llm"]
            config.llm.api_base = llm.get("api_base", config.llm.api_base)
            config.llm.api_key = llm.get("api_key", config.llm.api_key)
            config.llm.model = llm.get("model", config.llm.model)
            config.llm.temperature = llm.get("temperature", config.llm.temperature)
            if "max_tokens" in llm:
                config.llm.max_tokens = llm["max_tokens"]
            if "timeout" in llm:
                config.llm.timeout = llm["timeout"]

        # Apply agent settings
        if "agent" in profile_data:
            agent = profile_data["agent"]
            if "timeout_seconds" in agent:
                config.agent.timeout_seconds = agent["timeout_seconds"]
            if "max_retries" in agent:
                config.agent.max_retries = agent["max_retries"]
            if "failure_limit" in agent:
                config.agent.failure_limit = agent["failure_limit"]
            config.agent.enable_thinking = agent.get("enable_thinking", config.agent.enable_thinking)
            if "thinking_budget" in agent:
                config.agent.thinking_budget = agent["thinking_budget"]
            config.agent.parallel_tool_calls = agent.get("parallel_tool_calls", config.agent.parallel_tool_calls)
            config.agent.fallback_mode = agent.get("fallback_mode", config.agent.fallback_mode)
            config.agent.streaming = agent.get("streaming", config.agent.streaming)
            config.agent.permission_mode = agent.get("permission_mode", config.agent.permission_mode)

    def list_profiles(self) -> list[dict]:
        """List all available profiles.

        Returns:
            List of profile info dicts with name and is_current flag
        """
        profiles = []

        for profile_file in sorted(self.profiles_dir.glob("*.json")):
            name = profile_file.stem
            is_current = (name == self.current_profile)

            # Load profile to get info
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)

                profiles.append({
                    "name": name,
                    "is_current": is_current,
                    "model": data.get("llm", {}).get("model", "unknown"),
                    "api_base": data.get("llm", {}).get("api_base", "unknown"),
                })
            except Exception:
                # Skip invalid profiles
                continue

        return profiles

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: Profile name

        Returns:
            True if deleted, False if not found
        """
        profile_file = self.profiles_dir / f"{name}.json"

        if not profile_file.exists():
            return False

        profile_file.unlink()

        # Clear current if we deleted it
        if self.current_profile == name:
            self._save_current_profile(None)

        return True

    def get_current_profile(self) -> Optional[str]:
        """Get the name of the currently active profile.

        Returns:
            Profile name or None
        """
        return self.current_profile
