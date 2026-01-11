"""Storage layer for memory system - handles JSON file operations."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class MemoryStorage:
    """Handles reading and writing memories to ~/.athena/user_profile.json"""

    def __init__(self, profile_path: Optional[Path] = None):
        """Initialize storage with optional custom path.

        Args:
            profile_path: Optional path to profile JSON. Defaults to ~/.athena/user_profile.json
        """
        if profile_path is None:
            # Default to ~/.athena/user_profile.json
            home = Path.home()
            athena_dir = home / ".athena"
            athena_dir.mkdir(exist_ok=True)
            profile_path = athena_dir / "user_profile.json"

        self.profile_path = profile_path

    def load(self) -> dict:
        """Load user profile from JSON file.

        Returns:
            Dictionary containing user profile and memories.
            Returns default structure if file doesn't exist.
        """
        if not self.profile_path.exists():
            return self._default_profile()

        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate structure
            if "version" not in data or "memories" not in data:
                return self._default_profile()

            return data

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load user profile: {e}")
            return self._default_profile()

    def save(self, data: dict) -> bool:
        """Save user profile to JSON file.

        Args:
            data: Dictionary containing user profile and memories

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Update last_updated timestamp
            if "user" in data:
                data["user"]["last_updated"] = datetime.now().isoformat()

            # Create backup of existing file
            if self.profile_path.exists():
                backup_path = self.profile_path.with_suffix(".json.bak")
                self.profile_path.rename(backup_path)

            # Write new file
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except (IOError, OSError) as e:
            print(f"Error: Could not save user profile: {e}")
            # Restore backup if it exists
            backup_path = self.profile_path.with_suffix(".json.bak")
            if backup_path.exists():
                backup_path.rename(self.profile_path)
            return False

    def _default_profile(self) -> dict:
        """Create default profile structure.

        Returns:
            Default profile dictionary
        """
        return {
            "version": "1.0",
            "user": {
                "name": None,
                "timezone": None,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            },
            "memories": [],
        }

    def get_next_memory_id(self, data: dict) -> str:
        """Generate next memory ID.

        Args:
            data: Current profile data

        Returns:
            Next memory ID in format "mem_NNN"
        """
        if not data.get("memories"):
            return "mem_001"

        # Find highest existing ID
        max_id = 0
        for memory in data["memories"]:
            mem_id = memory.get("id", "mem_000")
            if mem_id.startswith("mem_"):
                try:
                    num = int(mem_id.split("_")[1])
                    max_id = max(max_id, num)
                except (ValueError, IndexError):
                    pass

        return f"mem_{max_id + 1:03d}"

    def backup(self) -> bool:
        """Create a timestamped backup of the profile.

        Returns:
            True if backup created successfully
        """
        if not self.profile_path.exists():
            return False

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.profile_path.with_suffix(f".{timestamp}.json")

            with open(self.profile_path, "r", encoding="utf-8") as source:
                data = json.load(source)

            with open(backup_path, "w", encoding="utf-8") as dest:
                json.dump(data, dest, indent=2, ensure_ascii=False)

            return True

        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not create backup: {e}")
            return False
