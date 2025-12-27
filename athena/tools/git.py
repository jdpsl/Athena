"""Git version control tools."""

import asyncio
from pathlib import Path
from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class GitStatusTool(Tool):
    """Tool for checking git status."""

    @property
    def name(self) -> str:
        return "GitStatus"

    @property
    def description(self) -> str:
        return """Check the status of the git repository.

Shows:
- Modified files
- Staged files
- Untracked files
- Current branch
- Commits ahead/behind remote

Better than plain 'git status' because it's parsed and formatted."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to git repository (defaults to current directory)",
                required=False,
            ),
        ]

    async def execute(self, path: str = ".", **kwargs: Any) -> ToolResult:
        """Execute git status."""
        try:
            # Run git status with porcelain format for parsing
            process = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                "--branch",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Git status failed: {stderr.decode()}",
                )

            # Parse status output
            lines = stdout.decode().strip().split("\n")
            branch_info = lines[0] if lines else ""
            file_statuses = lines[1:] if len(lines) > 1 else []

            # Format output
            output_lines = []

            # Branch info
            if branch_info.startswith("##"):
                branch = branch_info[3:].strip()
                output_lines.append(f"Branch: {branch}")

            # File statuses
            if file_statuses:
                staged = []
                modified = []
                untracked = []

                for line in file_statuses:
                    if not line.strip():
                        continue

                    status = line[:2]
                    filename = line[3:]

                    if status[0] in ["A", "M", "D", "R", "C"]:
                        staged.append(f"{status} {filename}")
                    if status[1] in ["M", "D"]:
                        modified.append(filename)
                    if status == "??":
                        untracked.append(filename)

                if staged:
                    output_lines.append("\nStaged:")
                    output_lines.extend(f"  {f}" for f in staged)

                if modified:
                    output_lines.append("\nModified:")
                    output_lines.extend(f"  {f}" for f in modified)

                if untracked:
                    output_lines.append("\nUntracked:")
                    output_lines.extend(f"  {f}" for f in untracked)
            else:
                output_lines.append("\nWorking tree clean")

            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                metadata={
                    "staged_count": len([l for l in file_statuses if l[:2][0] in ["A", "M", "D", "R", "C"]]),
                    "modified_count": len([l for l in file_statuses if l[:2][1] in ["M", "D"]]),
                    "untracked_count": len([l for l in file_statuses if l[:2] == "??"]),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git status failed: {str(e)}",
            )


class GitDiffTool(Tool):
    """Tool for viewing git diffs."""

    @property
    def name(self) -> str:
        return "GitDiff"

    @property
    def description(self) -> str:
        return """View git diff of changes.

Shows what changed in files. Can show:
- Unstaged changes (default)
- Staged changes (--staged)
- Specific files
- Specific commits

Better than 'git diff' because output is formatted and can be filtered."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Specific file to diff (optional, shows all if not provided)",
                required=False,
            ),
            ToolParameter(
                name="staged",
                type=ToolParameterType.BOOLEAN,
                description="Show staged changes instead of unstaged",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to git repository",
                required=False,
            ),
        ]

    async def execute(
        self,
        file_path: Optional[str] = None,
        staged: bool = False,
        path: str = ".",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute git diff."""
        try:
            args = ["git", "diff"]

            if staged:
                args.append("--staged")

            if file_path:
                args.append(file_path)

            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Git diff failed: {stderr.decode()}",
                )

            diff_output = stdout.decode()

            if not diff_output:
                return ToolResult(
                    success=True,
                    output="No changes" + (" staged" if staged else ""),
                )

            # Truncate if too long
            if len(diff_output) > 10000:
                diff_output = diff_output[:10000] + "\n\n[Diff truncated - too long]"

            return ToolResult(
                success=True,
                output=diff_output,
                metadata={"staged": staged, "file": file_path},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git diff failed: {str(e)}",
            )


class GitCommitTool(Tool):
    """Tool for creating git commits."""

    @property
    def name(self) -> str:
        return "GitCommit"

    @property
    def description(self) -> str:
        return """Create a git commit with staged changes.

IMPORTANT: Only commits files that are already staged.
Use GitStatus to see what's staged, or use 'git add' via Bash first.

Creates a commit with the given message."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="message",
                type=ToolParameterType.STRING,
                description="Commit message",
                required=True,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to git repository",
                required=False,
            ),
        ]

    async def execute(
        self, message: str, path: str = ".", **kwargs: Any
    ) -> ToolResult:
        """Execute git commit."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode() + stderr.decode()

            if process.returncode != 0:
                # Check if it's because nothing is staged
                if "nothing to commit" in output or "no changes added" in output:
                    return ToolResult(
                        success=False,
                        output=output,
                        error="Nothing staged to commit. Use 'git add' via Bash first.",
                    )
                return ToolResult(
                    success=False,
                    output=output,
                    error="Git commit failed",
                )

            return ToolResult(
                success=True,
                output=output,
                metadata={"message": message},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git commit failed: {str(e)}",
            )


class GitLogTool(Tool):
    """Tool for viewing git log."""

    @property
    def name(self) -> str:
        return "GitLog"

    @property
    def description(self) -> str:
        return """View git commit history.

Shows recent commits with:
- Commit hash
- Author
- Date
- Message

Useful for understanding recent changes or finding commit messages to follow."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="count",
                type=ToolParameterType.NUMBER,
                description="Number of commits to show (default: 10)",
                required=False,
                default=10,
            ),
            ToolParameter(
                name="file_path",
                type=ToolParameterType.STRING,
                description="Show log for specific file only",
                required=False,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to git repository",
                required=False,
            ),
        ]

    async def execute(
        self,
        count: int = 10,
        file_path: Optional[str] = None,
        path: str = ".",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute git log."""
        try:
            args = [
                "git",
                "log",
                f"-{count}",
                "--pretty=format:%h - %an, %ar : %s",
            ]

            if file_path:
                args.append(file_path)

            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Git log failed: {stderr.decode()}",
                )

            log_output = stdout.decode()

            if not log_output:
                return ToolResult(
                    success=True,
                    output="No commits found",
                )

            return ToolResult(
                success=True,
                output=log_output,
                metadata={"count": count, "file": file_path},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git log failed: {str(e)}",
            )


class GitBranchTool(Tool):
    """Tool for git branch operations."""

    @property
    def name(self) -> str:
        return "GitBranch"

    @property
    def description(self) -> str:
        return """List, create, or switch git branches.

Operations:
- list: Show all branches (default)
- create: Create new branch
- switch: Switch to existing branch
- delete: Delete a branch"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type=ToolParameterType.STRING,
                description="Action to perform",
                required=False,
                default="list",
                enum=["list", "create", "switch", "delete"],
            ),
            ToolParameter(
                name="branch_name",
                type=ToolParameterType.STRING,
                description="Branch name (required for create/switch/delete)",
                required=False,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to git repository",
                required=False,
            ),
        ]

    async def execute(
        self,
        action: str = "list",
        branch_name: Optional[str] = None,
        path: str = ".",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute git branch operation."""
        try:
            if action == "list":
                args = ["git", "branch", "-a"]
            elif action == "create":
                if not branch_name:
                    return ToolResult(
                        success=False,
                        output="",
                        error="branch_name required for create action",
                    )
                args = ["git", "branch", branch_name]
            elif action == "switch":
                if not branch_name:
                    return ToolResult(
                        success=False,
                        output="",
                        error="branch_name required for switch action",
                    )
                args = ["git", "checkout", branch_name]
            elif action == "delete":
                if not branch_name:
                    return ToolResult(
                        success=False,
                        output="",
                        error="branch_name required for delete action",
                    )
                args = ["git", "branch", "-d", branch_name]
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown action: {action}",
                )

            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode() + stderr.decode()

            if process.returncode != 0:
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"Git branch {action} failed",
                )

            return ToolResult(
                success=True,
                output=output.strip(),
                metadata={"action": action, "branch": branch_name},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git branch operation failed: {str(e)}",
            )
