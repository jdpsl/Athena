"""Memory search tool - allows agents to query user memories."""

from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class MemorySearchTool(Tool):
    """Search user memories and preferences.

    Allows agents to actively query the memory system when they need
    specific information about the user's preferences, system environment,
    or personal context.
    """

    def __init__(self, memory_manager=None):
        """Initialize with memory manager.

        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager

    @property
    def name(self) -> str:
        return "MemorySearch"

    @property
    def description(self) -> str:
        return """Search user memories and preferences stored across sessions.

Use this tool when you need to:
- Find out user's name or personal information
- Check coding preferences or patterns
- Look up system environment constraints (python vs python3, package managers, etc.)
- Search for project-specific patterns

The search is flexible and matches individual words, not just exact phrases.
For example, searching "name" will find "My name is Jeff".

Examples:
- User's name: query="name", type="personal"
- Check Python: query="python", type="coding"
- System commands: query="python3", type="environment"
- Testing tools: query="test"
- Communication style: query="concise", type="communication"

Search tips:
- Use simple keywords: "name" instead of "user name"
- Single words work best: "python", "test", "docker"
- Omit type to search all memories

Memory types:
- personal: Name, family, interests, background
- coding: Language, framework, testing preferences
- environment: System commands, package managers, tool availability
- communication: Response style preferences
- project: Project-specific patterns

Returns matching memories with their content, type, and tags."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type=ToolParameterType.STRING,
                description="Search query to find in memory content, tags, or type",
                required=True,
            ),
            ToolParameter(
                name="memory_type",
                type=ToolParameterType.STRING,
                description="Optional: Filter by memory type (personal, coding, environment, communication, project)",
                required=False,
            ),
        ]

    async def execute(self, query: str, memory_type: Optional[str] = None, **kwargs: Any) -> ToolResult:
        """Search memories by query and optional type filter.

        Args:
            query: Search query string
            memory_type: Optional memory type filter
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with matching memories
        """
        if not self.memory_manager:
            return ToolResult(
                success=False,
                output="",
                error="Memory manager not initialized",
            )

        try:
            # Search memories with improved flexibility
            if memory_type:
                # Filter by type first, then search within with word matching
                all_memories = self.memory_manager.list_memories(filter_type=memory_type)
                query_lower = query.lower()
                query_words = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]

                results = []
                for m in all_memories:
                    content = m.get("content", "").lower()
                    mem_type = m.get("type", "").lower()
                    tags = [t.lower() for t in m.get("tags", [])]

                    # Try exact match first
                    if query_lower in content or query_lower in mem_type:
                        results.append(m)
                        continue

                    # Try word-by-word match
                    if query_words:
                        for word in query_words:
                            if (word in content or
                                word in mem_type or
                                any(word in tag for tag in tags)):
                                results.append(m)
                                break
            else:
                # Use general search with user field checking
                results = self.memory_manager.search_memories(query, include_user_fields=True)

            if not results:
                return ToolResult(
                    success=True,
                    output=f"No memories found matching '{query}'" +
                           (f" with type '{memory_type}'" if memory_type else ""),
                    metadata={
                        "query": query,
                        "memory_type": memory_type,
                        "count": 0,
                    },
                )

            # Format results
            output_lines = [f"Found {len(results)} matching memor{'y' if len(results) == 1 else 'ies'}:\n"]

            for mem in results:
                mem_id = mem.get("id", "unknown")
                mem_type = mem.get("type", "unknown")
                content = mem.get("content", "")
                tags = mem.get("tags", [])
                inject_for = mem.get("inject_for", [])

                output_lines.append(f"[{mem_id}] ({mem_type})")
                output_lines.append(f"  Content: {content}")
                if tags:
                    output_lines.append(f"  Tags: {', '.join(tags)}")
                output_lines.append(f"  Visible to: {', '.join(inject_for)} agents")
                output_lines.append("")

            output = "\n".join(output_lines)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "query": query,
                    "memory_type": memory_type,
                    "count": len(results),
                    "results": [
                        {
                            "id": m.get("id"),
                            "type": m.get("type"),
                            "content": m.get("content"),
                        }
                        for m in results
                    ],
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Memory search failed: {str(e)}",
            )
