"""Search tools."""

import re
from pathlib import Path
from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class GlobTool(Tool):
    """Tool for finding files by pattern."""

    @property
    def name(self) -> str:
        return "Glob"

    @property
    def description(self) -> str:
        return "Fast file pattern matching. Supports glob patterns like '**/*.js' or 'src/**/*.ts'."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type=ToolParameterType.STRING,
                description="Glob pattern to match files against (e.g., '**/*.py')",
                required=True,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Directory to search in (defaults to current directory)",
                required=False,
            ),
        ]

    async def execute(
        self, pattern: str, path: Optional[str] = None, **kwargs: Any
    ) -> ToolResult:
        """Execute glob search."""
        try:
            search_path = Path(path).resolve() if path else Path.cwd()

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path not found: {path}",
                )

            # Find matching files
            matches = sorted(
                search_path.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Filter out directories, only return files
            file_matches = [str(p) for p in matches if p.is_file()]

            if not file_matches:
                output = f"No files found matching pattern: {pattern}"
            else:
                output = "\n".join(file_matches)

            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(file_matches), "pattern": pattern},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Glob search failed: {str(e)}",
            )


class GrepTool(Tool):
    """Tool for searching file contents."""

    @property
    def name(self) -> str:
        return "Grep"

    @property
    def description(self) -> str:
        return "Powerful content search. Supports regex patterns and various output modes."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type=ToolParameterType.STRING,
                description="Regular expression pattern to search for",
                required=True,
            ),
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="File or directory to search in (defaults to current directory)",
                required=False,
            ),
            ToolParameter(
                name="glob",
                type=ToolParameterType.STRING,
                description="Glob pattern to filter files (e.g., '*.py')",
                required=False,
            ),
            ToolParameter(
                name="output_mode",
                type=ToolParameterType.STRING,
                description="Output mode: 'content', 'files_with_matches', or 'count'",
                required=False,
                enum=["content", "files_with_matches", "count"],
            ),
            ToolParameter(
                name="case_insensitive",
                type=ToolParameterType.BOOLEAN,
                description="Case insensitive search",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="context_lines",
                type=ToolParameterType.NUMBER,
                description="Number of context lines to show around matches",
                required=False,
                default=0,
            ),
        ]

    async def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: str = "files_with_matches",
        case_insensitive: bool = False,
        context_lines: int = 0,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute grep search."""
        try:
            search_path = Path(path).resolve() if path else Path.cwd()

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path not found: {path}",
                )

            # Compile regex pattern
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)

            # Determine files to search
            if search_path.is_file():
                files = [search_path]
            else:
                glob_pattern = glob or "**/*"
                files = [f for f in search_path.glob(glob_pattern) if f.is_file()]

            # Search files
            results = []
            total_matches = 0

            for file_path in files:
                try:
                    # Skip binary files
                    if not self._is_text_file(file_path):
                        continue

                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()

                    # Find matches
                    file_matches = []
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            file_matches.append((i + 1, line.rstrip()))
                            total_matches += 1

                    if file_matches:
                        if output_mode == "files_with_matches":
                            results.append(str(file_path))
                        elif output_mode == "count":
                            results.append(f"{file_path}: {len(file_matches)}")
                        elif output_mode == "content":
                            for line_num, line_content in file_matches:
                                results.append(f"{file_path}:{line_num}: {line_content}")
                                # Limit results to prevent huge outputs
                                if len(results) >= 1000:
                                    break

                        # Break outer loop if we hit limit
                        if len(results) >= 1000:
                            break

                except Exception:
                    # Skip files that can't be read
                    continue

            if not results:
                output = f"No matches found for pattern: {pattern}"
            else:
                if len(results) >= 1000:
                    output = "\n".join(results[:1000]) + f"\n\n... (truncated, showing first 1000 of {len(results)} results)"
                else:
                    output = "\n".join(results)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "total_matches": total_matches,
                    "files_matched": len(results) if output_mode == "files_with_matches" else len(set(r.split(":")[0] for r in results)),
                    "pattern": pattern,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Grep search failed: {str(e)}",
            )

    @staticmethod
    def _is_text_file(path: Path) -> bool:
        """Check if a file is likely a text file."""
        # Simple heuristic: check first 512 bytes for null bytes
        try:
            with open(path, "rb") as f:
                chunk = f.read(512)
                return b"\x00" not in chunk
        except Exception:
            return False
