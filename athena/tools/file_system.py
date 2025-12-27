"""File system operation tools."""

import os
import shutil
from pathlib import Path
from typing import Any, Optional
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


class DeleteFileTool(Tool):
    """Tool for deleting files or directories."""

    @property
    def name(self) -> str:
        return "DeleteFile"

    @property
    def description(self) -> str:
        return """Delete a file or directory.

IMPORTANT: This is permanent! Use with caution.

Can delete:
- Single files
- Empty directories
- Non-empty directories (with recursive=True)

Safer than 'rm' because it validates paths and prevents accidents."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to file or directory to delete",
                required=True,
            ),
            ToolParameter(
                name="recursive",
                type=ToolParameterType.BOOLEAN,
                description="Delete directories recursively (required for non-empty dirs)",
                required=False,
                default=False,
            ),
        ]

    async def execute(
        self, path: str, recursive: bool = False, **kwargs: Any
    ) -> ToolResult:
        """Execute file deletion."""
        try:
            target = Path(path).expanduser().resolve()

            if not target.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path does not exist: {path}",
                )

            # Safety check: don't delete critical paths
            critical_paths = [Path.home(), Path("/"), Path.cwd()]
            if target in critical_paths:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Cannot delete critical path: {path}",
                )

            if target.is_file():
                target.unlink()
                return ToolResult(
                    success=True,
                    output=f"Deleted file: {path}",
                    metadata={"path": str(target), "type": "file"},
                )

            elif target.is_dir():
                if recursive:
                    shutil.rmtree(target)
                    return ToolResult(
                        success=True,
                        output=f"Deleted directory recursively: {path}",
                        metadata={"path": str(target), "type": "directory", "recursive": True},
                    )
                else:
                    # Try to remove empty directory
                    try:
                        target.rmdir()
                        return ToolResult(
                            success=True,
                            output=f"Deleted empty directory: {path}",
                            metadata={"path": str(target), "type": "directory"},
                        )
                    except OSError:
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"Directory not empty. Use recursive=True to delete: {path}",
                        )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to delete: {str(e)}",
            )


class MoveFileTool(Tool):
    """Tool for moving/renaming files."""

    @property
    def name(self) -> str:
        return "MoveFile"

    @property
    def description(self) -> str:
        return """Move or rename a file or directory.

Can be used for:
- Renaming files
- Moving files to different directories
- Moving entire directories

Safer than 'mv' because it validates paths and prevents overwrites."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="source",
                type=ToolParameterType.STRING,
                description="Source path",
                required=True,
            ),
            ToolParameter(
                name="destination",
                type=ToolParameterType.STRING,
                description="Destination path",
                required=True,
            ),
            ToolParameter(
                name="overwrite",
                type=ToolParameterType.BOOLEAN,
                description="Overwrite destination if it exists",
                required=False,
                default=False,
            ),
        ]

    async def execute(
        self, source: str, destination: str, overwrite: bool = False, **kwargs: Any
    ) -> ToolResult:
        """Execute file move."""
        try:
            src = Path(source).expanduser().resolve()
            dst = Path(destination).expanduser().resolve()

            if not src.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Source does not exist: {source}",
                )

            if dst.exists() and not overwrite:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Destination exists. Use overwrite=True to replace: {destination}",
                )

            # Perform move
            shutil.move(str(src), str(dst))

            return ToolResult(
                success=True,
                output=f"Moved: {source} → {destination}",
                metadata={"source": str(src), "destination": str(dst)},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to move: {str(e)}",
            )


class CopyFileTool(Tool):
    """Tool for copying files or directories."""

    @property
    def name(self) -> str:
        return "CopyFile"

    @property
    def description(self) -> str:
        return """Copy a file or directory.

Can copy:
- Single files
- Entire directories (with recursive=True)

Creates parent directories if needed."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="source",
                type=ToolParameterType.STRING,
                description="Source path",
                required=True,
            ),
            ToolParameter(
                name="destination",
                type=ToolParameterType.STRING,
                description="Destination path",
                required=True,
            ),
            ToolParameter(
                name="recursive",
                type=ToolParameterType.BOOLEAN,
                description="Copy directories recursively",
                required=False,
                default=False,
            ),
        ]

    async def execute(
        self, source: str, destination: str, recursive: bool = False, **kwargs: Any
    ) -> ToolResult:
        """Execute file copy."""
        try:
            src = Path(source).expanduser().resolve()
            dst = Path(destination).expanduser().resolve()

            if not src.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Source does not exist: {source}",
                )

            # Create parent directories
            dst.parent.mkdir(parents=True, exist_ok=True)

            if src.is_file():
                shutil.copy2(str(src), str(dst))
                return ToolResult(
                    success=True,
                    output=f"Copied file: {source} → {destination}",
                    metadata={"source": str(src), "destination": str(dst), "type": "file"},
                )

            elif src.is_dir():
                if recursive:
                    shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
                    return ToolResult(
                        success=True,
                        output=f"Copied directory: {source} → {destination}",
                        metadata={"source": str(src), "destination": str(dst), "type": "directory"},
                    )
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Source is a directory. Use recursive=True: {source}",
                    )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to copy: {str(e)}",
            )


class ListDirTool(Tool):
    """Tool for listing directory contents."""

    @property
    def name(self) -> str:
        return "ListDir"

    @property
    def description(self) -> str:
        return """List contents of a directory.

Shows:
- Files and directories
- File sizes
- Permissions
- Modification times (optional)

Better than 'ls' because output is structured and filterable."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Directory to list (defaults to current directory)",
                required=False,
            ),
            ToolParameter(
                name="show_hidden",
                type=ToolParameterType.BOOLEAN,
                description="Show hidden files (starting with .)",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="recursive",
                type=ToolParameterType.BOOLEAN,
                description="List subdirectories recursively",
                required=False,
                default=False,
            ),
        ]

    async def execute(
        self,
        path: str = ".",
        show_hidden: bool = False,
        recursive: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute directory listing."""
        try:
            target = Path(path).expanduser().resolve()

            if not target.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory does not exist: {path}",
                )

            if not target.is_dir():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a directory: {path}",
                )

            output_lines = [f"Contents of {target}:\n"]

            if recursive:
                # Recursive listing
                for root, dirs, files in os.walk(target):
                    root_path = Path(root)
                    rel_path = root_path.relative_to(target)

                    # Filter hidden if needed
                    if not show_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        files = [f for f in files if not f.startswith(".")]

                    if str(rel_path) != ".":
                        output_lines.append(f"\n{rel_path}/")

                    for file in sorted(files):
                        file_path = root_path / file
                        size = file_path.stat().st_size
                        output_lines.append(f"  {file} ({self._format_size(size)})")

            else:
                # Single directory listing
                items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name))

                for item in items:
                    # Skip hidden files if requested
                    if not show_hidden and item.name.startswith("."):
                        continue

                    if item.is_dir():
                        output_lines.append(f"  [DIR]  {item.name}/")
                    else:
                        size = item.stat().st_size
                        output_lines.append(f"  [FILE] {item.name} ({self._format_size(size)})")

            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                metadata={"path": str(target), "recursive": recursive},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to list directory: {str(e)}",
            )

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class MakeDirTool(Tool):
    """Tool for creating directories."""

    @property
    def name(self) -> str:
        return "MakeDir"

    @property
    def description(self) -> str:
        return """Create a new directory.

Creates:
- Single directory
- Nested directories (with parents=True)

Safe operation - doesn't fail if directory exists."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to directory to create",
                required=True,
            ),
            ToolParameter(
                name="parents",
                type=ToolParameterType.BOOLEAN,
                description="Create parent directories as needed",
                required=False,
                default=True,
            ),
        ]

    async def execute(
        self, path: str, parents: bool = True, **kwargs: Any
    ) -> ToolResult:
        """Execute directory creation."""
        try:
            target = Path(path).expanduser().resolve()

            if target.exists():
                if target.is_dir():
                    return ToolResult(
                        success=True,
                        output=f"Directory already exists: {path}",
                        metadata={"path": str(target), "created": False},
                    )
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Path exists but is not a directory: {path}",
                    )

            target.mkdir(parents=parents, exist_ok=True)

            return ToolResult(
                success=True,
                output=f"Created directory: {path}",
                metadata={"path": str(target), "created": True},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to create directory: {str(e)}",
            )
