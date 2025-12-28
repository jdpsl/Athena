"""Skill loader for discovering and loading skills."""

import logging
from pathlib import Path
from typing import Optional
from athena.skills.skill import Skill

logger = logging.getLogger(__name__)


class SkillLoader:
    """Loads skills from .athena/skills/ directories."""

    def __init__(self, working_directory: Optional[str] = None):
        """Initialize skill loader.

        Args:
            working_directory: Current working directory for project skills
        """
        self.working_directory = Path(working_directory or ".").resolve()
        self.skills: dict[str, Skill] = {}

    def discover_skills(self) -> dict[str, Skill]:
        """Discover skills from global and project locations.

        Checks in order:
        1. ~/.athena/skills/ (global skills)
        2. {working_dir}/.athena/skills/ (project skills)

        Project skills override global skills with the same name.

        Returns:
            Dictionary mapping skill names to Skill objects
        """
        self.skills = {}

        # Load global skills from ~/.athena/skills/
        global_skills_dir = Path.home() / ".athena" / "skills"
        if global_skills_dir.exists():
            self._load_skills_from_directory(global_skills_dir, scope="global")

        # Load project skills from .athena/skills/
        project_skills_dir = self.working_directory / ".athena" / "skills"
        if project_skills_dir.exists():
            self._load_skills_from_directory(project_skills_dir, scope="project")

        logger.info(f"Discovered {len(self.skills)} skill(s)")
        return self.skills

    def _load_skills_from_directory(self, skills_dir: Path, scope: str) -> None:
        """Load all skills from a directory.

        Args:
            skills_dir: Directory containing skill subdirectories
            scope: Scope name for logging (global/project)
        """
        if not skills_dir.is_dir():
            return

        # Each skill is a subdirectory with SKILL.md
        for skill_folder in skills_dir.iterdir():
            if not skill_folder.is_dir():
                continue

            skill_file = skill_folder / "SKILL.md"
            if not skill_file.exists():
                logger.warning(f"Skipping {skill_folder.name}: missing SKILL.md")
                continue

            try:
                skill = Skill.from_markdown(skill_file)

                # Warn if overriding existing skill
                if skill.name in self.skills:
                    logger.info(
                        f"Skill '{skill.name}' from {scope} overrides previous definition"
                    )

                self.skills[skill.name] = skill
                logger.debug(f"Loaded skill '{skill.name}' from {scope}: {skill_file}")

            except Exception as e:
                logger.error(f"Failed to load skill from {skill_file}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name.

        Args:
            name: Skill name

        Returns:
            Skill if found, None otherwise
        """
        return self.skills.get(name)

    def list_skills(self) -> list[Skill]:
        """Get all loaded skills.

        Returns:
            List of all skills
        """
        return list(self.skills.values())
