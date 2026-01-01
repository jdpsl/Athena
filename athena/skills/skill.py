"""Skill class for reusable agent behaviors."""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A reusable agent behavior loaded from SKILL.md."""

    name: str = Field(description="Skill identifier (lowercase, hyphens, numbers)")
    description: str = Field(description="What the skill does and when to use it")
    instructions: str = Field(description="Markdown instructions for Claude")
    allowed_tools: list[str] = Field(default_factory=list, description="Tools allowed without permission")
    model: Optional[str] = Field(default=None, description="Optional model override")
    api_base: Optional[str] = Field(default=None, description="Optional API base URL override")
    skill_path: Path = Field(description="Path to the SKILL.md file")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_markdown(cls, skill_path: Path) -> "Skill":
        """Parse SKILL.md file with YAML frontmatter.

        Args:
            skill_path: Path to SKILL.md file

        Returns:
            Skill instance

        Raises:
            ValueError: If SKILL.md is malformed
        """
        if not skill_path.exists():
            raise ValueError(f"Skill file not found: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")

        # Split frontmatter and instructions
        if not content.startswith("---"):
            raise ValueError(f"SKILL.md must start with YAML frontmatter: {skill_path}")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid SKILL.md format (missing closing ---): {skill_path}")

        frontmatter_str = parts[1].strip()
        instructions = parts[2].strip()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {skill_path}: {e}")

        # Validate required fields
        if "name" not in frontmatter:
            raise ValueError(f"SKILL.md missing required field 'name': {skill_path}")
        if "description" not in frontmatter:
            raise ValueError(f"SKILL.md missing required field 'description': {skill_path}")

        # Parse allowed-tools
        allowed_tools = []
        if "allowed-tools" in frontmatter:
            tools_str = frontmatter["allowed-tools"]
            if isinstance(tools_str, str):
                allowed_tools = [t.strip() for t in tools_str.split(",") if t.strip()]
            elif isinstance(tools_str, list):
                allowed_tools = tools_str

        return cls(
            name=frontmatter["name"],
            description=frontmatter["description"],
            instructions=instructions,
            allowed_tools=allowed_tools,
            model=frontmatter.get("model"),
            api_base=frontmatter.get("api_base"),
            skill_path=skill_path,
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this skill.

        Returns:
            Complete system prompt with instructions
        """
        prompt = f"# {self.name.replace('-', ' ').title()}\n\n"
        prompt += f"{self.instructions}\n"
        return prompt
