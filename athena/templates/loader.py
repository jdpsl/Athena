"""Template loader and renderer for project initialization."""

import yaml
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class FileTemplate:
    """Represents a file to be generated from a template."""

    path: str  # Target path (can include variables like {{project_name}})
    template: str  # Path to template file
    content: Optional[str] = None  # Direct content (alternative to template file)


@dataclass
class ProjectTemplate:
    """Represents a complete project template."""

    name: str
    type: str
    description: str
    directories: List[str] = field(default_factory=list)
    files: List[FileTemplate] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)


class TemplateLoader:
    """Load and render project templates."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize template loader.

        Args:
            template_dir: Base directory for templates. Defaults to athena/templates/
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(__file__).parent

        # Also check user templates
        self.user_template_dir = Path.home() / ".athena" / "templates"

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates.

        Returns:
            List of dicts with template info: {name, type, description, path}
        """
        templates = []

        # Check both system and user templates
        for base_dir in [self.template_dir, self.user_template_dir]:
            if not base_dir.exists():
                continue

            # Find all structure.yaml files
            for structure_file in base_dir.rglob("structure.yaml"):
                try:
                    template = self._load_structure_yaml(structure_file)
                    templates.append({
                        "name": template.name,
                        "type": template.type,
                        "description": template.description,
                        "path": str(structure_file.parent)
                    })
                except Exception:
                    # Skip invalid templates
                    pass

        return templates

    def load_template(self, template_type: str) -> Optional[ProjectTemplate]:
        """Load a template by type.

        Args:
            template_type: Template type (e.g., "python-web", "node-cli")

        Returns:
            ProjectTemplate or None if not found
        """
        # Check user templates first (allows override)
        for base_dir in [self.user_template_dir, self.template_dir]:
            structure_file = self._find_template_structure(base_dir, template_type)
            if structure_file:
                return self._load_structure_yaml(structure_file)

        return None

    def _find_template_structure(self, base_dir: Path, template_type: str) -> Optional[Path]:
        """Find structure.yaml for a template type.

        Args:
            base_dir: Base directory to search
            template_type: Template type to find

        Returns:
            Path to structure.yaml or None
        """
        if not base_dir.exists():
            return None

        # Map template type to directory path
        # e.g., "python-web" -> python/web/structure.yaml
        parts = template_type.split("-")
        if len(parts) >= 2:
            language = parts[0]
            project_type = parts[1]
            structure_file = base_dir / language / project_type / "structure.yaml"
            if structure_file.exists():
                return structure_file

        return None

    def _load_structure_yaml(self, structure_file: Path) -> ProjectTemplate:
        """Load a structure.yaml file into a ProjectTemplate.

        Args:
            structure_file: Path to structure.yaml

        Returns:
            ProjectTemplate
        """
        with open(structure_file, 'r') as f:
            data = yaml.safe_load(f)

        # Parse file templates
        files = []
        for file_data in data.get("files", []):
            if isinstance(file_data, dict):
                files.append(FileTemplate(
                    path=file_data.get("path", ""),
                    template=file_data.get("template", ""),
                    content=file_data.get("content")
                ))

        return ProjectTemplate(
            name=data.get("name", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            directories=data.get("directories", []),
            files=files,
            next_steps=data.get("next_steps", []),
            dependencies=data.get("dependencies", {})
        )

    def render_template(
        self,
        template: ProjectTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render a template with variables.

        Args:
            template: ProjectTemplate to render
            variables: Variables for substitution (e.g., {project_name: "my-app"})

        Returns:
            Dict mapping file paths to file contents
        """
        rendered_files = {}
        template_base_dir = None

        # Find the base directory for this template
        for base_dir in [self.user_template_dir, self.template_dir]:
            structure_file = self._find_template_structure(base_dir, template.type)
            if structure_file:
                template_base_dir = structure_file.parent
                break

        if not template_base_dir:
            return rendered_files

        # Render each file
        for file_template in template.files:
            # Render the target path
            target_path = self._substitute_variables(file_template.path, variables)

            # Get content - either from direct content or template file
            if file_template.content:
                content = file_template.content
            elif file_template.template:
                # Substitute variables in template path (e.g., LICENSE.{{license}})
                template_file_path = self._substitute_variables(file_template.template, variables)

                # Load template file
                template_path = self.template_dir / template_file_path
                if not template_path.exists():
                    # Try relative to template directory
                    template_path = template_base_dir / template_file_path

                if template_path.exists():
                    with open(template_path, 'r') as f:
                        content = f.read()
                else:
                    content = ""
            else:
                content = ""

            # Substitute variables in content
            rendered_content = self._substitute_variables(content, variables)
            rendered_files[target_path] = rendered_content

        return rendered_files

    def render_directories(
        self,
        template: ProjectTemplate,
        variables: Dict[str, Any]
    ) -> List[str]:
        """Render directory list with variables substituted.

        Args:
            template: ProjectTemplate
            variables: Variables for substitution

        Returns:
            List of directory paths
        """
        return [
            self._substitute_variables(dir_path, variables)
            for dir_path in template.directories
        ]

    def render_next_steps(
        self,
        template: ProjectTemplate,
        variables: Dict[str, Any]
    ) -> List[str]:
        """Render next steps with variables substituted.

        Args:
            template: ProjectTemplate
            variables: Variables for substitution

        Returns:
            List of next step instructions
        """
        return [
            self._substitute_variables(step, variables)
            for step in template.next_steps
        ]

    @staticmethod
    def _substitute_variables(text: str, variables: Dict[str, Any]) -> str:
        """Substitute {{variable}} patterns in text.

        Args:
            text: Text with {{variable}} patterns
            variables: Dict of variable values

        Returns:
            Text with variables substituted
        """
        result = text
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
