"""Memory manager - high-level API for memory operations."""

from datetime import datetime
from typing import Optional
from pathlib import Path

from athena.memory.storage import MemoryStorage
from athena.memory.detector import MemoryDetector


class MemoryManager:
    """High-level memory management API."""

    def __init__(self, profile_path: Optional[Path] = None):
        """Initialize memory manager.

        Args:
            profile_path: Optional path to profile JSON
        """
        self.storage = MemoryStorage(profile_path)
        self.detector = MemoryDetector()

    def add_memory(
        self,
        content: str,
        source: str = "manual",
        mem_type: Optional[str] = None,
        inject_for: Optional[list[str]] = None,
    ) -> dict:
        """Add a new memory.

        Args:
            content: Memory content text
            source: How memory was created ("manual", "explicit", "implicit")
            mem_type: Optional memory type override
            inject_for: Optional inject_for override

        Returns:
            The created memory dict
        """
        data = self.storage.load()

        # Auto-detect type and inject_for if not provided
        if mem_type is None or inject_for is None:
            detected_type, detected_inject, tags = self.detector.detect_type(content)
            mem_type = mem_type or detected_type
            inject_for = inject_for or detected_inject
        else:
            tags = []

        # Generate memory ID
        mem_id = self.storage.get_next_memory_id(data)

        # Create memory object
        memory = {
            "id": mem_id,
            "type": mem_type,
            "content": content,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "confidence": 1.0 if source in ["manual", "explicit"] else 0.8,
            "inject_for": inject_for,
            "tags": tags,
        }

        # Check if we should extract name
        if mem_type == "personal":
            name = self.detector.extract_name(content)
            if name and not data["user"].get("name"):
                data["user"]["name"] = name

        # Add to memories list
        data["memories"].append(memory)

        # Save
        self.storage.save(data)

        return memory

    def list_memories(self, filter_type: Optional[str] = None) -> list[dict]:
        """List all memories, optionally filtered by type.

        Args:
            filter_type: Optional type to filter by ("coding", "personal", etc.)

        Returns:
            List of memory dictionaries
        """
        data = self.storage.load()
        memories = data.get("memories", [])

        if filter_type:
            # Map friendly names to actual types
            type_map = {
                "coding": ["coding_preference", "avoid_pattern", "project_pattern"],
                "personal": ["personal"],
                "communication": ["communication"],
                "environment": ["environment"],
                "system": ["environment"],
            }

            if filter_type in type_map:
                filter_types = type_map[filter_type]
                memories = [m for m in memories if m.get("type") in filter_types]
            else:
                # Exact type match
                memories = [m for m in memories if m.get("type") == filter_type]

        return memories

    def get_memory(self, mem_id: str) -> Optional[dict]:
        """Get a specific memory by ID.

        Args:
            mem_id: Memory ID

        Returns:
            Memory dict or None if not found
        """
        data = self.storage.load()
        for memory in data.get("memories", []):
            if memory.get("id") == mem_id:
                return memory
        return None

    def delete_memory(self, mem_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            mem_id: Memory ID to delete

        Returns:
            True if deleted, False if not found
        """
        data = self.storage.load()
        memories = data.get("memories", [])

        # Find and remove
        for i, memory in enumerate(memories):
            if memory.get("id") == mem_id:
                memories.pop(i)
                data["memories"] = memories
                self.storage.save(data)
                return True

        return False

    def search_memories(self, query: str, include_user_fields: bool = False) -> list[dict]:
        """Search memories by content with flexible word matching.

        Args:
            query: Search query (can be phrase or individual words)
            include_user_fields: If True, also search structured user fields

        Returns:
            List of matching memory dictionaries, or dict with user info if found
        """
        data = self.storage.load()
        memories = data.get("memories", [])
        query_lower = query.lower()

        # Split query into words for flexible matching
        query_words = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]

        # Check structured user fields first if requested
        if include_user_fields:
            user_data = data.get("user", {})

            # Check if query is asking for name
            if any(word in ["name", "called"] for word in query_words):
                user_name = user_data.get("name")
                if user_name:
                    # Return a synthetic "memory" with user's name
                    return [{
                        "id": "user_name",
                        "type": "personal",
                        "content": f"My name is {user_name}",
                        "source": "user_profile",
                        "inject_for": ["planning", "research"],
                        "tags": ["personal", "name"],
                        "is_user_field": True,
                    }]

            # Check timezone
            if any(word in ["timezone", "time", "zone"] for word in query_words):
                timezone = user_data.get("timezone")
                if timezone:
                    return [{
                        "id": "user_timezone",
                        "type": "personal",
                        "content": f"My timezone is {timezone}",
                        "source": "user_profile",
                        "inject_for": ["planning", "research"],
                        "tags": ["personal", "timezone"],
                        "is_user_field": True,
                    }]

        # Search in memories with flexible word matching
        results = []
        for memory in memories:
            content = memory.get("content", "").lower()
            mem_type = memory.get("type", "").lower()
            tags = [t.lower() for t in memory.get("tags", [])]

            # Try exact phrase match first (highest priority)
            if query_lower in content or query_lower in mem_type:
                results.append(memory)
                continue

            # Try word-by-word matching
            if query_words:
                # Match if ANY query word appears in content, type, or tags
                matched = False
                for word in query_words:
                    if (word in content or
                        word in mem_type or
                        any(word in tag for tag in tags)):
                        matched = True
                        break

                if matched:
                    results.append(memory)

        return results

    def get_memories_for_agent(self, agent_type: str) -> list[dict]:
        """Get memories that should be injected for a specific agent type.

        Args:
            agent_type: Agent type ("coding", "planning", "research")

        Returns:
            List of memories for this agent
        """
        data = self.storage.load()
        memories = data.get("memories", [])

        # Filter by inject_for
        return [
            m for m in memories
            if agent_type in m.get("inject_for", [])
        ]

    def get_user_info(self) -> dict:
        """Get user information.

        Returns:
            User info dictionary
        """
        data = self.storage.load()
        return data.get("user", {})

    def update_memory(
        self,
        mem_id: str,
        content: Optional[str] = None,
        inject_for: Optional[list[str]] = None,
    ) -> bool:
        """Update an existing memory.

        Args:
            mem_id: Memory ID
            content: New content (optional)
            inject_for: New inject_for list (optional)

        Returns:
            True if updated, False if not found
        """
        data = self.storage.load()
        memories = data.get("memories", [])

        for memory in memories:
            if memory.get("id") == mem_id:
                if content is not None:
                    memory["content"] = content
                    # Re-detect type and tags if content changed
                    mem_type, detected_inject, tags = self.detector.detect_type(content)
                    memory["type"] = mem_type
                    memory["tags"] = tags
                    if inject_for is None:
                        memory["inject_for"] = detected_inject

                if inject_for is not None:
                    memory["inject_for"] = inject_for

                memory["last_updated"] = datetime.now().isoformat()

                self.storage.save(data)
                return True

        return False

    def get_stats(self) -> dict:
        """Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        data = self.storage.load()
        memories = data.get("memories", [])

        # Count by type
        type_counts = {}
        for memory in memories:
            mem_type = memory.get("type", "unknown")
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

        # Count by agent
        agent_counts = {"coding": 0, "planning": 0, "research": 0}
        for memory in memories:
            for agent in memory.get("inject_for", []):
                if agent in agent_counts:
                    agent_counts[agent] += 1

        return {
            "total": len(memories),
            "by_type": type_counts,
            "by_agent": agent_counts,
            "user": data.get("user", {}),
        }

    def get_stale_memories(self, months: int = 6) -> list[dict]:
        """Get memories that are older than specified months.

        Args:
            months: Age threshold in months (default 6)

        Returns:
            List of memories that are stale (older than threshold)
        """
        from datetime import datetime, timedelta

        data = self.storage.load()
        memories = data.get("memories", [])

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=months * 30)

        stale = []
        for memory in memories:
            # Check last_updated first, fall back to created_at
            date_str = memory.get("last_updated") or memory.get("created_at")
            if date_str:
                try:
                    mem_date = datetime.fromisoformat(date_str)
                    if mem_date < cutoff_date:
                        # Add age info to memory
                        age_days = (datetime.now() - mem_date).days
                        memory_with_age = memory.copy()
                        memory_with_age["age_days"] = age_days
                        memory_with_age["age_months"] = age_days // 30
                        stale.append(memory_with_age)
                except (ValueError, TypeError):
                    pass

        return stale
