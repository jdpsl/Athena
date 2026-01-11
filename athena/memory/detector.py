"""Memory type detector - automatically categorizes memories."""

import re
from typing import Tuple


class MemoryDetector:
    """Detects memory type and assigns appropriate inject_for agents."""

    # Keywords for each memory type
    CODING_KEYWORDS = [
        # Languages
        "typescript", "javascript", "python", "rust", "go", "java", "kotlin", "swift",
        "c++", "c#", "ruby", "php", "scala", "elixir",
        # Frameworks/Libraries
        "react", "vue", "angular", "svelte", "fastapi", "flask", "django", "express",
        "spring", "rails", "laravel", "nextjs", "gatsby",
        # Tools
        "pytest", "jest", "mocha", "junit", "vscode", "vim", "emacs", "pycharm",
        "docker", "kubernetes", "git", "npm", "pnpm", "yarn", "pip", "cargo",
        # Patterns/Practices
        "functional", "object-oriented", "async", "await", "promise", "callback",
        "type hint", "annotation", "decorator", "interface", "class", "function",
        "camelcase", "snake_case", "pascalcase", "kebab-case",
        # Testing/Quality
        "test", "testing", "tdd", "lint", "format", "black", "ruff", "eslint",
        "prettier", "mypy", "coverage",
        # Concepts
        "prefer", "use", "framework", "library", "language", "code", "coding",
        "programming", "development", "build", "compile", "deploy"
    ]

    PERSONAL_KEYWORDS = [
        # Family
        "kid", "kids", "child", "children", "son", "daughter", "family",
        "spouse", "partner", "parent",
        # Interests
        "hobby", "interest", "love", "enjoy", "passion", "fan of",
        # Background
        "work at", "working at", "job", "role", "position", "company",
        "teach", "teacher", "engineer", "developer", "designer",
        "freelance", "consultant", "student", "learning",
        # Personal info
        "my name", "i'm", "i am", "timezone", "location", "live in",
    ]

    COMMUNICATION_KEYWORDS = [
        "concise", "brief", "verbose", "detailed", "explain",
        "emoji", "emojis", "tone", "style", "format",
        "bullet", "numbered", "response", "output",
    ]

    AVOID_KEYWORDS = [
        "never", "don't", "do not", "avoid", "no", "not",
        "hate", "dislike", "against", "refuse", "won't",
    ]

    ENVIRONMENT_KEYWORDS = [
        # Command availability
        "python3", "python2", "pip3", "pip2", "node", "npm", "npx",
        "command not found", "not found", "not available", "not installed",
        "use instead", "instead of", "available", "installed",
        # System constraints
        "system packages", "system python", "break", "breaks", "venv", "virtualenv",
        "conda", "permission", "sudo", "root", "administrator",
        # Package managers
        "brew", "apt", "apt-get", "yum", "dnf", "pacman", "choco",
        # Platform/OS
        "macos", "linux", "ubuntu", "debian", "fedora", "arch", "windows",
        "wsl", "this system", "this machine", "environment",
        # Paths and tools
        "path", "binary", "executable", "shell", "bash", "zsh", "fish",
        "$PATH", "homebrew", "requires", "need to",
    ]

    def detect_type(self, content: str) -> Tuple[str, list[str], list[str]]:
        """Detect memory type from content.

        Args:
            content: The memory text

        Returns:
            Tuple of (type, inject_for, tags)
            - type: "coding_preference", "personal", "communication", "project_pattern", "avoid_pattern", or "environment"
            - inject_for: List of agent types that should see this memory
            - tags: List of relevant tags for organization
        """
        content_lower = content.lower()
        tags = []

        # Check for avoid patterns first (they can be coding or other)
        has_avoid = any(keyword in content_lower for keyword in self.AVOID_KEYWORDS)

        # Count keyword matches for each type
        environment_matches = sum(1 for kw in self.ENVIRONMENT_KEYWORDS if kw in content_lower)
        coding_matches = sum(1 for kw in self.CODING_KEYWORDS if kw in content_lower)
        personal_matches = sum(1 for kw in self.PERSONAL_KEYWORDS if kw in content_lower)
        communication_matches = sum(1 for kw in self.COMMUNICATION_KEYWORDS if kw in content_lower)

        # Determine primary type - environment takes priority since it's critical for commands
        if environment_matches >= 2:  # Need at least 2 matches to avoid false positives
            mem_type = "environment"
            tags.append("environment")
            tags.append("system")

            # Extract specific environment tags
            if "python" in content_lower:
                tags.append("python")
            if any(kw in content_lower for kw in ["pip", "venv", "conda"]):
                tags.append("packages")
            if any(kw in content_lower for kw in ["sudo", "permission", "root"]):
                tags.append("permissions")
            if any(kw in content_lower for kw in ["brew", "apt", "yum", "pacman"]):
                tags.append("package-manager")

            # Environment info for coding and planning agents (they run commands)
            inject_for = ["coding", "planning"]

        elif coding_matches > max(personal_matches, communication_matches):
            if has_avoid:
                mem_type = "avoid_pattern"
                tags.append("avoid")
            else:
                mem_type = "coding_preference"
            tags.append("coding")

            # Extract specific coding tags
            for keyword in self.CODING_KEYWORDS:
                if keyword in content_lower:
                    tags.append(keyword)

            # Coding preferences go to all agents
            inject_for = ["coding", "planning", "research"]

        elif personal_matches > communication_matches:
            mem_type = "personal"
            tags.append("personal")

            # Detect subcategories
            if any(kw in content_lower for kw in ["kid", "kids", "child", "children", "son", "daughter"]):
                tags.append("family")
            if any(kw in content_lower for kw in ["hobby", "interest", "love", "enjoy", "passion"]):
                tags.append("interests")
            if any(kw in content_lower for kw in ["work", "job", "company", "role"]):
                tags.append("background")

            # Personal info only for planning and research
            inject_for = ["planning", "research"]

        elif communication_matches > 0:
            mem_type = "communication"
            tags.append("communication")
            tags.append("style")

            # Communication preferences for all agents
            inject_for = ["coding", "planning", "research"]

        else:
            # Default: treat as general project pattern
            mem_type = "project_pattern"
            tags.append("project")

            # Project patterns for planning and coding
            inject_for = ["coding", "planning"]

        # Remove duplicate tags
        tags = list(set(tags))

        return mem_type, inject_for, tags

    def extract_name(self, content: str) -> str | None:
        """Try to extract user's name from content.

        Args:
            content: The memory text

        Returns:
            Name if found, None otherwise
        """
        # Patterns like "My name is X", "I'm X", "Call me X"
        patterns = [
            r"my name is (\w+)",
            r"i'?m (\w+)",
            r"call me (\w+)",
            r"name: (\w+)",
        ]

        content_lower = content.lower()
        for pattern in patterns:
            match = re.search(pattern, content_lower)
            if match:
                # Return capitalized name
                return match.group(1).capitalize()

        return None

    def should_merge_with_existing(self, new_content: str, existing_content: str) -> bool:
        """Determine if new memory should merge with existing one.

        Args:
            new_content: New memory content
            existing_content: Existing memory content

        Returns:
            True if they should be merged (similar topics)
        """
        # Simple check: if they share 50%+ of meaningful words, they're related
        new_words = set(re.findall(r'\b\w{4,}\b', new_content.lower()))
        existing_words = set(re.findall(r'\b\w{4,}\b', existing_content.lower()))

        if not new_words or not existing_words:
            return False

        overlap = len(new_words & existing_words)
        similarity = overlap / min(len(new_words), len(existing_words))

        return similarity > 0.5
