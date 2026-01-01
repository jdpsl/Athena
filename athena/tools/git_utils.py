"""Git workflow utilities for professional commit messages and branch naming."""

from typing import Optional, Tuple


class CommitMessageBuilder:
    """Build professional commit messages using conventional commit format."""

    # Valid commit types
    VALID_TYPES = [
        "feat",      # New feature
        "fix",       # Bug fix
        "docs",      # Documentation only changes
        "style",     # Formatting, missing semi colons, etc; no code change
        "refactor",  # Refactoring production code
        "test",      # Adding tests, refactoring tests; no production code change
        "chore",     # Updating build tasks, package manager configs, etc; no production code change
        "perf",      # Performance improvements
        "ci",        # CI related changes
        "build",     # Build system changes
        "revert",    # Revert a previous commit
    ]

    @staticmethod
    def build_conventional_commit(
        type: str,
        description: str,
        scope: Optional[str] = None,
        body: Optional[str] = None,
        breaking: bool = False,
        footer: Optional[str] = None,
    ) -> str:
        """Build a conventional commit message.

        Format: <type>(<scope>): <description>

        [optional body]

        [optional footer]

        Args:
            type: Commit type (feat, fix, docs, etc.)
            description: Short description of the change
            scope: Optional scope (component/module affected)
            body: Optional longer description
            breaking: Whether this is a breaking change
            footer: Optional footer (e.g., issue references)

        Returns:
            Formatted commit message
        """
        # Validate type
        if type not in CommitMessageBuilder.VALID_TYPES:
            type = "chore"  # Default to chore if invalid

        # Build header: type(scope): description
        header = type
        if scope:
            header += f"({scope})"
        if breaking:
            header += "!"
        header += f": {description}"

        # Build full message
        parts = [header]

        if body:
            parts.append("")
            parts.append(body)

        if footer:
            parts.append("")
            parts.append(footer)

        return "\n".join(parts)

    @staticmethod
    def suggest_type_from_files(files: list[str]) -> str:
        """Suggest commit type based on changed files.

        Args:
            files: List of changed file paths

        Returns:
            Suggested commit type
        """
        # Analyze file patterns
        has_tests = any("test" in f.lower() for f in files)
        has_docs = any(f.lower().endswith((".md", ".rst", ".txt")) or "readme" in f.lower() for f in files)
        has_config = any(f.lower().endswith((".yaml", ".yml", ".json", ".toml", ".ini")) or "config" in f.lower() for f in files)
        has_ci = any(".github" in f or ".gitlab" in f or "ci" in f.lower() for f in files)
        has_build = any("setup" in f.lower() or "package" in f.lower() or "requirements" in f.lower() for f in files)

        # Return most specific match
        if has_ci:
            return "ci"
        elif has_build:
            return "build"
        elif has_tests and not any(f.endswith((".py", ".js", ".ts", ".go")) and "test" not in f.lower() for f in files):
            return "test"  # Only test files
        elif has_docs and len(files) == len([f for f in files if f.lower().endswith((".md", ".rst", ".txt"))]):
            return "docs"  # Only docs
        elif has_config:
            return "chore"
        else:
            return "feat"  # Default to feat for code changes

    @staticmethod
    def suggest_commit_message(
        files: list[str],
        type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Generate a suggested conventional commit message.

        Args:
            files: List of changed files
            type: Optional explicit type (auto-detected if not provided)
            description: Optional explicit description

        Returns:
            Suggested commit message
        """
        if not type:
            type = CommitMessageBuilder.suggest_type_from_files(files)

        if not description:
            # Generate description based on type
            if type == "test":
                description = "Add/update tests"
            elif type == "docs":
                description = "Update documentation"
            elif type == "chore":
                description = "Update configuration"
            elif type == "ci":
                description = "Update CI configuration"
            elif type == "build":
                description = "Update build configuration"
            else:
                description = "Add new changes"

        return CommitMessageBuilder.build_conventional_commit(
            type=type,
            description=description,
        )


class BranchNameValidator:
    """Validate and suggest branch names following conventions."""

    # Valid prefixes for branch names
    VALID_PREFIXES = [
        "feature/",
        "feat/",
        "bugfix/",
        "fix/",
        "hotfix/",
        "chore/",
        "docs/",
        "test/",
        "refactor/",
        "release/",
    ]

    @staticmethod
    def validate(branch_name: str) -> Tuple[bool, str]:
        """Validate branch name against conventions.

        Args:
            branch_name: Branch name to validate

        Returns:
            Tuple of (is_valid, message)
        """
        # Check for valid prefix
        if not any(branch_name.startswith(prefix) for prefix in BranchNameValidator.VALID_PREFIXES):
            suggestions = "\n".join(
                f"  - {prefix}{branch_name}"
                for prefix in ["feature/", "bugfix/", "hotfix/", "chore/"]
            )
            return False, f"Branch name should start with a conventional prefix:\n{suggestions}"

        # Check for spaces
        if " " in branch_name:
            fixed = branch_name.replace(" ", "-")
            return False, f"Branch name cannot contain spaces. Try: {fixed}"

        # Check for invalid characters
        invalid_chars = ["~", "^", ":", "\\", "?", "*", "["]
        for char in invalid_chars:
            if char in branch_name:
                return False, f"Branch name contains invalid character: '{char}'"

        # Check length
        if len(branch_name) > 50:
            return False, "Branch name is too long (max 50 characters)"

        # Check for empty slug after prefix
        for prefix in BranchNameValidator.VALID_PREFIXES:
            if branch_name == prefix:
                return False, f"Branch name cannot be just '{prefix}' - add a description"

        return True, "✓ Valid branch name"

    @staticmethod
    def suggest(description: str) -> str:
        """Suggest a branch name from a description.

        Args:
            description: Human-readable description of the branch purpose

        Returns:
            Suggested branch name
        """
        # Convert to lowercase
        slug = description.lower()

        # Replace spaces and special chars with dashes
        slug = slug.replace(" ", "-")
        slug = slug.replace("_", "-")
        for char in [".", ",", "!", "?", ":", ";", "(", ")", "[", "]", "{", "}"]:
            slug = slug.replace(char, "")

        # Remove consecutive dashes
        while "--" in slug:
            slug = slug.replace("--", "-")

        # Trim dashes from ends
        slug = slug.strip("-")

        # Truncate if too long (leaving room for prefix)
        if len(slug) > 40:
            slug = slug[:40].rsplit("-", 1)[0]  # Cut at word boundary

        # Detect type from keywords
        description_lower = description.lower()

        # Check for hotfix first (critical issues)
        if any(word in description_lower for word in ["critical", "urgent", "production", "hotfix", "security", "emergency"]):
            return f"hotfix/{slug}"
        # Then regular bugfix
        elif any(word in description_lower for word in ["fix", "bug", "broke", "error", "issue"]):
            return f"bugfix/{slug}"
        elif any(word in description_lower for word in ["doc", "readme", "guide", "manual"]):
            return f"docs/{slug}"
        elif any(word in description_lower for word in ["test", "testing", "spec"]):
            return f"test/{slug}"
        elif any(word in description_lower for word in ["refactor", "restructure", "reorganize"]):
            return f"refactor/{slug}"
        elif any(word in description_lower for word in ["chore", "config", "setup", "dependency", "dependencies", "package", "upgrade"]):
            return f"chore/{slug}"
        elif any(word in description_lower for word in ["release", "version"]):
            return f"release/{slug}"
        else:
            return f"feature/{slug}"

    @staticmethod
    def format(branch_name: str) -> str:
        """Format a branch name to follow conventions.

        Args:
            branch_name: Raw branch name

        Returns:
            Formatted branch name
        """
        # Check if already has a valid prefix
        has_prefix = any(branch_name.startswith(prefix) for prefix in BranchNameValidator.VALID_PREFIXES)

        if has_prefix:
            # Just clean up the slug part
            parts = branch_name.split("/", 1)
            if len(parts) == 2:
                prefix, slug = parts
                slug = slug.lower().replace(" ", "-")
                return f"{prefix}{slug}"

        # No prefix - suggest one
        return BranchNameValidator.suggest(branch_name)
