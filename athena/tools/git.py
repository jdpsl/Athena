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
    """Tool for creating git commits with pre-commit hook handling."""

    @property
    def name(self) -> str:
        return "GitCommit"

    @property
    def description(self) -> str:
        return """Create a git commit with staged changes.

IMPORTANT: Only commits files that are already staged.
Use GitStatus to see what's staged, or use 'git add' via Bash first.

Features:
- Automatically handles pre-commit hooks
- Auto-amends if hooks modify files (e.g., formatters)
- Clear errors if hooks reject (e.g., linters)
- Validates authorship before amending"""

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
        """Execute git commit with hook handling."""
        try:
            # Attempt commit
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

            # Commit failed
            if process.returncode != 0:
                # Check for "nothing to commit"
                if "nothing to commit" in output or "no changes added" in output:
                    return ToolResult(
                        success=False,
                        output=output,
                        error="Nothing staged to commit. Use 'git add' via Bash first.",
                    )

                # Check for pre-commit hook rejection
                if "pre-commit" in output.lower() or "hook" in output.lower():
                    return ToolResult(
                        success=False,
                        output=output,
                        error="❌ Pre-commit hook rejected the commit. Fix the issues and try again.",
                        metadata={"hook_failed": True},
                    )

                return ToolResult(
                    success=False,
                    output=output,
                    error="Git commit failed",
                )

            # Commit succeeded - check if pre-commit hook modified files
            modified_files = await self._get_modified_files(path)

            if modified_files:
                # Hook auto-modified files (e.g., Black, Prettier)
                # Stage them and amend the commit
                stage_result = await self._stage_files(modified_files, path)
                if not stage_result:
                    return ToolResult(
                        success=True,
                        output=output + "\n\n⚠️  Pre-commit hook modified files, but failed to stage them.",
                        metadata={"hook_modified": True},
                    )

                # Check if safe to amend
                can_amend, amend_msg = await self._can_amend_safely(path)
                if not can_amend:
                    return ToolResult(
                        success=True,
                        output=output + f"\n\n⚠️  Pre-commit hook modified files:\n{chr(10).join(modified_files)}\n\n{amend_msg}\nStage and commit again manually.",
                        metadata={"hook_modified": True, "amend_blocked": True},
                    )

                # Safe to amend
                amend_result = await self._amend_commit(path)
                if amend_result.success:
                    return ToolResult(
                        success=True,
                        output=output + f"\n\n✓ Pre-commit hook modified files - automatically amended:\n{chr(10).join(modified_files)}",
                        metadata={"amended": True, "modified_files": modified_files},
                    )

            # Normal successful commit
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

    async def _get_modified_files(self, path: str) -> list[str]:
        """Get list of modified files after commit."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "diff", "--name-only",
                stdout=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, _ = await process.communicate()
            files = stdout.decode().strip()
            return files.split("\n") if files else []
        except:
            return []

    async def _stage_files(self, files: list[str], path: str) -> bool:
        """Stage modified files."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "add", *files,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def _amend_commit(self, path: str) -> ToolResult:
        """Amend the last commit (no-edit)."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "commit", "--amend", "--no-edit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            return ToolResult(
                success=process.returncode == 0,
                output=stdout.decode() + stderr.decode(),
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    async def _can_amend_safely(self, path: str) -> tuple[bool, str]:
        """Check if it's safe to amend the last commit."""
        try:
            # Check if commit has been pushed
            process = await asyncio.create_subprocess_exec(
                "git", "log", "@{u}..", "--oneline",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            # If no upstream or error, it's safe (not pushed)
            if process.returncode != 0:
                return True, "Safe to amend (not pushed)"

            # Check if there are unpushed commits
            unpushed_commits = stdout.decode().strip().split("\n")
            if len(unpushed_commits) > 0 and unpushed_commits[0]:
                return True, "Safe to amend (commits not yet pushed)"

            return False, "⚠️  Commit has been pushed to remote. Amending requires force push."

        except:
            # On error, be safe and allow amend
            return True, "Unable to check push status - assuming safe"


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


class GitPushTool(Tool):
    """Tool for pushing commits to remote with retry logic."""

    @property
    def name(self) -> str:
        return "GitPush"

    @property
    def description(self) -> str:
        return """Push commits to remote repository with automatic retry on network failures.

Features:
- Exponential backoff retry (up to 3 attempts)
- Safety check: prevents force push to main/master
- Helpful error messages for common issues
- Upstream tracking setup with -u flag

IMPORTANT: Only use force push when absolutely necessary and never on main/master."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="remote",
                type=ToolParameterType.STRING,
                description="Remote name (default: origin)",
                required=False,
                default="origin",
            ),
            ToolParameter(
                name="branch",
                type=ToolParameterType.STRING,
                description="Branch name to push (defaults to current branch)",
                required=False,
            ),
            ToolParameter(
                name="set_upstream",
                type=ToolParameterType.BOOLEAN,
                description="Set upstream tracking (-u flag)",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="force",
                type=ToolParameterType.BOOLEAN,
                description="Force push (DANGEROUS - blocked for main/master)",
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
        remote: str = "origin",
        branch: Optional[str] = None,
        set_upstream: bool = False,
        force: bool = False,
        path: str = ".",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute git push with retry logic."""
        try:
            # Get current branch if not specified
            if not branch:
                branch = await self._get_current_branch(path)
                if not branch:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Could not determine current branch",
                    )

            # Safety check for force push
            if force:
                if branch in ["main", "master"]:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"⚠️  BLOCKED: Force push to '{branch}' is dangerous! Use a feature branch instead.",
                    )

            # Build git push command
            args = ["git", "push", remote, branch]

            if set_upstream:
                args.insert(2, "-u")  # Insert after "git push"

            if force:
                args.append("--force")

            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=path,
                )
                stdout, stderr = await process.communicate()

                output = stdout.decode() + stderr.decode()

                # Success
                if process.returncode == 0:
                    success_msg = output.strip()
                    if attempt > 0:
                        success_msg += f"\n✓ Succeeded after {attempt + 1} attempts"
                    return ToolResult(
                        success=True,
                        output=success_msg,
                        metadata={"attempts": attempt + 1, "branch": branch},
                    )

                # Check if it's a retryable network error
                if self._is_retryable_error(output):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        await asyncio.sleep(wait_time)
                        continue  # Retry

                # Non-retryable error - return immediately
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"Git push failed: {self._parse_error(output)}",
                )

            # Max retries exhausted
            return ToolResult(
                success=False,
                output=output,
                error=f"Git push failed after {max_retries} retries. Check network connection.",
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Git push failed: {str(e)}",
            )

    async def _get_current_branch(self, path: str) -> Optional[str]:
        """Get the current git branch name."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "branch", "--show-current",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, _ = await process.communicate()

            if process.returncode == 0:
                return stdout.decode().strip()
            return None
        except:
            return None

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if error should trigger retry."""
        retryable_patterns = [
            "connection reset",
            "could not resolve host",
            "failed to connect",
            "network is unreachable",
            "temporary failure",
            "timeout",
            "connection timed out",
            "operation timed out",
        ]
        error_lower = error_msg.lower()
        return any(pattern in error_lower for pattern in retryable_patterns)

    def _parse_error(self, error_msg: str) -> str:
        """Parse git push error and return user-friendly message."""
        error_lower = error_msg.lower()

        if "permission denied" in error_lower:
            return "Permission denied. Check your SSH keys or access token."
        elif "authentication failed" in error_lower:
            return "Authentication failed. Check your credentials."
        elif "remote rejected" in error_lower:
            return "Remote rejected the push. May need to pull first."
        elif "non-fast-forward" in error_lower:
            return "Push rejected (non-fast-forward). Pull changes first or use --force carefully."
        elif "no such remote" in error_lower:
            return f"Remote not found. Check remote name with 'git remote -v'."

        return error_msg.strip()


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


class GitCreatePRTool(Tool):
    """Tool for creating GitHub Pull Requests using gh CLI."""

    @property
    def name(self) -> str:
        return "GitCreatePR"

    @property
    def description(self) -> str:
        return """Create a GitHub Pull Request using gh CLI.

Requires:
- gh CLI installed (brew install gh)
- GitHub authentication (gh auth login)

Features:
- Auto-detects current branch
- Creates PR with title and description
- Supports draft PRs
- Returns PR URL on success"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type=ToolParameterType.STRING,
                description="Pull request title",
                required=True,
            ),
            ToolParameter(
                name="body",
                type=ToolParameterType.STRING,
                description="Pull request description/body",
                required=False,
            ),
            ToolParameter(
                name="base",
                type=ToolParameterType.STRING,
                description="Base branch (defaults to main/master)",
                required=False,
            ),
            ToolParameter(
                name="draft",
                type=ToolParameterType.BOOLEAN,
                description="Create as draft PR",
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
        title: str,
        body: str = "",
        base: Optional[str] = None,
        draft: bool = False,
        path: str = ".",
        **kwargs: Any,
    ) -> ToolResult:
        """Create a GitHub pull request."""
        try:
            # Build gh pr create command
            args = ["gh", "pr", "create", "--title", title]

            if body:
                args.extend(["--body", body])

            if base:
                args.extend(["--base", base])

            if draft:
                args.append("--draft")

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=path,
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            if process.returncode != 0:
                # Parse common errors
                if "gh: command not found" in error or "not found" in error.lower():
                    return ToolResult(
                        success=False,
                        output="",
                        error="gh CLI not installed. Install with: brew install gh",
                    )
                elif "not authenticated" in error.lower() or "authentication" in error.lower():
                    return ToolResult(
                        success=False,
                        output="",
                        error="Not authenticated with GitHub. Run: gh auth login",
                    )
                elif "no commits" in error.lower():
                    return ToolResult(
                        success=False,
                        output="",
                        error="No commits on current branch. Push commits first.",
                    )
                elif "already exists" in error.lower():
                    return ToolResult(
                        success=False,
                        output="",
                        error="A pull request already exists for this branch.",
                    )

                return ToolResult(
                    success=False,
                    output=error,
                    error=f"Failed to create PR: {error}",
                )

            # Success - extract PR URL
            pr_url = output

            return ToolResult(
                success=True,
                output=f"✓ Pull request created successfully!\n{pr_url}",
                metadata={"url": pr_url, "title": title, "draft": draft},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"PR creation failed: {str(e)}",
            )
