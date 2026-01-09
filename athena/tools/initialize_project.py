"""InitializeProject tool for creating professional project structures."""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult
from athena.templates.loader import TemplateLoader


class InitializeProjectTool(Tool):
    """Initialize a new project with professional structure and best practices."""

    def __init__(self):
        """Initialize the tool."""
        super().__init__()
        self.template_loader = TemplateLoader()

    @property
    def name(self) -> str:
        return "InitializeProject"

    @property
    def description(self) -> str:
        return """Initialize a new project with professional structure.

Creates:
- Directory structure (src/, tests/, docs/)
- README.md with comprehensive documentation
- .gitignore appropriate for the language
- LICENSE file
- Language-specific config files (pyproject.toml, package.json, etc.)
- Test setup
- CI/CD workflows
- Git initialization
- Optional: GitHub repository creation

This tool uses templates to ensure consistent, high-quality project setup."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="project_type",
                type=ToolParameterType.STRING,
                description="Type of project to create",
                required=True,
                enum=["python-web", "python-cli", "python-lib", "node-web", "node-cli"]
            ),
            ToolParameter(
                name="project_name",
                type=ToolParameterType.STRING,
                description="Project name (kebab-case recommended, e.g., 'my-project')",
                required=True
            ),
            ToolParameter(
                name="description",
                type=ToolParameterType.STRING,
                description="Brief project description",
                required=True
            ),
            ToolParameter(
                name="author",
                type=ToolParameterType.STRING,
                description="Author name",
                required=False
            ),
            ToolParameter(
                name="email",
                type=ToolParameterType.STRING,
                description="Author email",
                required=False
            ),
            ToolParameter(
                name="license",
                type=ToolParameterType.STRING,
                description="License type",
                required=False,
                enum=["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
            ),
            ToolParameter(
                name="init_git",
                type=ToolParameterType.BOOLEAN,
                description="Initialize git repository",
                required=False
            ),
            ToolParameter(
                name="create_github_repo",
                type=ToolParameterType.BOOLEAN,
                description="Create GitHub repository (requires gh CLI)",
                required=False
            ),
        ]

    async def execute(
        self,
        project_type: str,
        project_name: str,
        description: str,
        author: str = "Your Name",
        email: str = "you@example.com",
        license: str = "MIT",
        init_git: bool = True,
        create_github_repo: bool = False,
        **kwargs
    ) -> ToolResult:
        """Execute project initialization.

        Args:
            project_type: Type of project (python-web, node-web, etc.)
            project_name: Project name
            description: Project description
            author: Author name
            email: Author email
            license: License type
            init_git: Whether to initialize git
            create_github_repo: Whether to create GitHub repo
            **kwargs: Additional parameters

        Returns:
            ToolResult with success status and output
        """
        try:
            # Load template
            template = self.template_loader.load_template(project_type)
            if not template:
                return ToolResult(
                    success=False,
                    output=f"❌ Template not found for type: {project_type}"
                )

            # Prepare variables for template substitution
            project_name_snake = project_name.replace("-", "_").replace(" ", "_")
            variables = {
                "project_name": project_name,
                "project_name_snake": project_name_snake,
                "description": description,
                "author": author,
                "email": email,
                "license": license,
                "year": str(datetime.now().year),
            }

            # Create project directory
            project_path = Path.cwd() / project_name
            if project_path.exists():
                return ToolResult(
                    success=False,
                    output=f"❌ Directory already exists: {project_name}"
                )

            project_path.mkdir(parents=True)
            os.chdir(project_path)

            # Create directories
            directories = self.template_loader.render_directories(template, variables)
            for directory in directories:
                dir_path = project_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)

            # Create files from templates
            files = self.template_loader.render_template(template, variables)
            created_files = []
            for file_path, content in files.items():
                full_path = project_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                created_files.append(file_path)

            # Initialize git
            git_initialized = False
            if init_git:
                try:
                    subprocess.run(["git", "init"], check=True, capture_output=True)
                    subprocess.run(["git", "add", "."], check=True, capture_output=True)
                    subprocess.run(
                        ["git", "commit", "-m", f"feat: initialize {project_type} project"],
                        check=True,
                        capture_output=True
                    )
                    git_initialized = True
                except subprocess.CalledProcessError as e:
                    # Git initialization failed, but continue
                    pass

            # Create GitHub repository
            github_url = None
            if create_github_repo and git_initialized:
                try:
                    result = subprocess.run(
                        ["gh", "repo", "create", project_name, "--public", "--source=.", "--push"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    # Parse GitHub URL from output
                    output = result.stdout
                    if "https://github.com" in output:
                        github_url = [line for line in output.split("\n") if "https://github.com" in line][0].strip()
                except subprocess.CalledProcessError:
                    # GitHub creation failed, but continue
                    pass

            # Render next steps
            next_steps = self.template_loader.render_next_steps(template, variables)

            # Build output message
            output_lines = [
                f"✅ Project initialized: {project_name}",
                f"📁 Type: {template.name}",
                "",
                "📦 Created structure:",
            ]

            # Add directories
            for directory in directories[:5]:  # Show first 5
                output_lines.append(f"  ✓ {directory}/")
            if len(directories) > 5:
                output_lines.append(f"  ... and {len(directories) - 5} more directories")

            output_lines.append("")
            output_lines.append("📝 Generated files:")

            # Add files
            for file_path in created_files[:10]:  # Show first 10
                output_lines.append(f"  ✓ {file_path}")
            if len(created_files) > 10:
                output_lines.append(f"  ... and {len(created_files) - 10} more files")

            if git_initialized:
                output_lines.append("")
                output_lines.append("🔧 Git repository initialized")
                output_lines.append("  ✓ Initial commit created")

            if github_url:
                output_lines.append("")
                output_lines.append("🌐 GitHub repository created")
                output_lines.append(f"  {github_url}")

            output_lines.append("")
            output_lines.append("🚀 Next steps:")
            for i, step in enumerate(next_steps, 1):
                output_lines.append(f"  {i}. {step}")

            return ToolResult(
                success=True,
                output="\n".join(output_lines)
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"❌ Failed to initialize project: {str(e)}"
            )
