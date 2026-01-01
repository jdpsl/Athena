"""Jupyter Notebook tools for interactive development."""

import json
import os
from typing import Any, Optional, List
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult


def _format_source(content: str) -> List[str]:
    """Format content as Jupyter notebook source (list of strings with newlines).

    Jupyter notebooks store source as an array of strings where each line
    (except the last) ends with a newline character.

    Example:
        "line1\\nline2\\nline3" -> ["line1\\n", "line2\\n", "line3"]
    """
    if not content:
        return []

    lines = content.split('\n')
    # Add newline to all lines except the last
    return [line + '\n' for line in lines[:-1]] + [lines[-1]]


class NotebookReadTool(Tool):
    """Read and display Jupyter notebook contents.

    Shows all cells (code/markdown) with their outputs, making it easy to
    understand the notebook structure before editing.
    """

    @property
    def name(self) -> str:
        return "NotebookRead"

    @property
    def description(self) -> str:
        return """Read and display Jupyter notebook contents.

Shows:
- Cell numbers and types (code/markdown)
- Cell source code
- Execution outputs (text, tables, images metadata)
- Execution counts

Use this before editing notebooks to understand their structure.

Example: NotebookRead(path="analysis.ipynb")"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to .ipynb file",
                required=True,
            ),
        ]

    async def execute(self, path: str, **kwargs: Any) -> ToolResult:
        """Read notebook and display contents."""
        try:
            # Expand path
            path = os.path.expanduser(path)

            # Check file exists
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Notebook not found: {path}"
                )

            # Check it's a .ipynb file
            if not path.endswith('.ipynb'):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Not a Jupyter notebook file (expected .ipynb): {path}"
                )

            # Load notebook
            with open(path, 'r') as f:
                notebook = json.load(f)

            # Validate notebook structure
            if 'cells' not in notebook:
                return ToolResult(
                    success=False,
                    output="",
                    error="Invalid notebook format: missing 'cells' field"
                )

            # Format notebook contents
            output_lines = []
            output_lines.append(f"📓 Notebook: {os.path.basename(path)}")
            output_lines.append(f"Cells: {len(notebook['cells'])}")

            # Get kernel info if available
            kernel_spec = notebook.get('metadata', {}).get('kernelspec', {})
            if kernel_spec:
                kernel_name = kernel_spec.get('display_name', kernel_spec.get('name', 'Unknown'))
                output_lines.append(f"Kernel: {kernel_name}")

            output_lines.append("")
            output_lines.append("=" * 70)

            # Display each cell
            for i, cell in enumerate(notebook['cells']):
                cell_type = cell.get('cell_type', 'unknown')
                source = cell.get('source', [])

                # Convert source to string (can be list or string)
                if isinstance(source, list):
                    source_text = ''.join(source)
                else:
                    source_text = source

                output_lines.append("")
                output_lines.append(f"Cell {i} [{cell_type}]:")

                # Show execution count for code cells
                if cell_type == 'code':
                    exec_count = cell.get('execution_count')
                    if exec_count is not None:
                        output_lines.append(f"Execution count: {exec_count}")

                output_lines.append("")
                output_lines.append(source_text)

                # Show outputs for code cells
                if cell_type == 'code' and 'outputs' in cell:
                    outputs = cell['outputs']
                    if outputs:
                        output_lines.append("")
                        output_lines.append("Output:")
                        output_lines.append(self._format_outputs(outputs))

                output_lines.append("")
                output_lines.append("-" * 70)

            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                metadata={
                    "path": path,
                    "cell_count": len(notebook['cells']),
                    "kernel": kernel_spec.get('name') if kernel_spec else None,
                }
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid JSON in notebook file: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read notebook: {str(e)}"
            )

    def _format_outputs(self, outputs: List[dict]) -> str:
        """Format cell outputs for display."""
        result_lines = []

        for output in outputs:
            output_type = output.get('output_type', 'unknown')

            if output_type == 'stream':
                # stdout/stderr output
                text = output.get('text', [])
                if isinstance(text, list):
                    text = ''.join(text)
                result_lines.append(f"[stream:{output.get('name', 'stdout')}]")
                result_lines.append(text.rstrip())

            elif output_type == 'execute_result':
                # Result of expression
                data = output.get('data', {})
                if 'text/plain' in data:
                    text = data['text/plain']
                    if isinstance(text, list):
                        text = ''.join(text)
                    result_lines.append("[result]")
                    result_lines.append(text.rstrip())
                elif 'text/html' in data:
                    result_lines.append("[HTML output - not displayed]")
                elif 'image/png' in data:
                    result_lines.append("[PNG image - not displayed]")
                else:
                    result_lines.append(f"[{', '.join(data.keys())}]")

            elif output_type == 'display_data':
                # Display output (plots, images, etc.)
                data = output.get('data', {})
                if 'text/plain' in data:
                    text = data['text/plain']
                    if isinstance(text, list):
                        text = ''.join(text)
                    result_lines.append("[display]")
                    result_lines.append(text.rstrip())
                elif 'image/png' in data:
                    result_lines.append("[PNG image]")
                elif 'image/jpeg' in data:
                    result_lines.append("[JPEG image]")
                else:
                    result_lines.append(f"[display: {', '.join(data.keys())}]")

            elif output_type == 'error':
                # Error/traceback
                ename = output.get('ename', 'Error')
                evalue = output.get('evalue', '')
                result_lines.append(f"[error: {ename}]")
                result_lines.append(evalue)

                # Show traceback if available
                traceback = output.get('traceback', [])
                if traceback:
                    result_lines.append("")
                    result_lines.extend(traceback[:5])  # Limit traceback lines
                    if len(traceback) > 5:
                        result_lines.append(f"... ({len(traceback) - 5} more lines)")

        return "\n".join(result_lines) if result_lines else "[no output]"


class NotebookEditTool(Tool):
    """Edit Jupyter notebook cells.

    Allows replacing, inserting, or deleting cells in a notebook.
    Use NotebookRead first to see the cell structure.
    """

    @property
    def name(self) -> str:
        return "NotebookEdit"

    @property
    def description(self) -> str:
        return """Edit Jupyter notebook cells.

Actions:
- replace: Replace content of existing cell
- insert: Insert new cell at position
- delete: Remove a cell

IMPORTANT: Use NotebookRead first to see cell numbers!

Examples:
- Replace cell 2: NotebookEdit(path="analysis.ipynb", cell_number=2, content="import numpy as np")
- Insert markdown: NotebookEdit(path="analysis.ipynb", cell_number=1, action="insert", cell_type="markdown", content="# Introduction")
- Delete cell 5: NotebookEdit(path="analysis.ipynb", cell_number=5, action="delete")"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to .ipynb file",
                required=True,
            ),
            ToolParameter(
                name="cell_number",
                type=ToolParameterType.NUMBER,
                description="Cell index (0-based)",
                required=True,
            ),
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="New cell content (not needed for delete action)",
                required=False,
            ),
            ToolParameter(
                name="cell_type",
                type=ToolParameterType.STRING,
                description="Cell type: 'code' or 'markdown' (default: code)",
                required=False,
            ),
            ToolParameter(
                name="action",
                type=ToolParameterType.STRING,
                description="Action: 'replace', 'insert', or 'delete' (default: replace)",
                required=False,
            ),
        ]

    async def execute(
        self,
        path: str,
        cell_number: int,
        content: Optional[str] = None,
        cell_type: str = "code",
        action: str = "replace",
        **kwargs: Any
    ) -> ToolResult:
        """Edit notebook cell."""
        try:
            # Expand path
            path = os.path.expanduser(path)

            # Check file exists
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Notebook not found: {path}"
                )

            # Validate action
            if action not in ['replace', 'insert', 'delete']:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid action '{action}'. Must be: replace, insert, or delete"
                )

            # Validate cell type
            if cell_type not in ['code', 'markdown']:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid cell_type '{cell_type}'. Must be: code or markdown"
                )

            # Load notebook
            with open(path, 'r') as f:
                notebook = json.load(f)

            cells = notebook.get('cells', [])

            # Validate cell number
            if action == 'insert':
                # For insert, cell_number can be 0 to len(cells)
                if cell_number < 0 or cell_number > len(cells):
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Invalid cell_number {cell_number}. Must be 0-{len(cells)} for insert"
                    )
            else:
                # For replace/delete, must be existing cell
                if cell_number < 0 or cell_number >= len(cells):
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Invalid cell_number {cell_number}. Notebook has {len(cells)} cells (0-{len(cells)-1})"
                    )

            # Perform action
            if action == 'replace':
                if content is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="content parameter required for replace action"
                    )

                cells[cell_number]['cell_type'] = cell_type
                cells[cell_number]['source'] = _format_source(content)

                # Reset outputs for code cells
                if cell_type == 'code':
                    cells[cell_number]['outputs'] = []
                    cells[cell_number]['execution_count'] = None
                else:
                    # Markdown cells don't have outputs
                    cells[cell_number].pop('outputs', None)
                    cells[cell_number].pop('execution_count', None)

                result_msg = f"Replaced cell {cell_number} ({cell_type})"

            elif action == 'insert':
                if content is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="content parameter required for insert action"
                    )

                new_cell = {
                    'cell_type': cell_type,
                    'metadata': {},
                    'source': _format_source(content)
                }

                if cell_type == 'code':
                    new_cell['outputs'] = []
                    new_cell['execution_count'] = None

                cells.insert(cell_number, new_cell)
                result_msg = f"Inserted {cell_type} cell at position {cell_number}"

            elif action == 'delete':
                del cells[cell_number]
                result_msg = f"Deleted cell {cell_number}"

            # Update notebook
            notebook['cells'] = cells

            # Save notebook
            with open(path, 'w') as f:
                json.dump(notebook, f, indent=1)

            return ToolResult(
                success=True,
                output=result_msg,
                metadata={
                    "path": path,
                    "action": action,
                    "cell_number": cell_number,
                    "total_cells": len(cells)
                }
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid JSON in notebook file: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to edit notebook: {str(e)}"
            )


class NotebookExecuteTool(Tool):
    """Execute Jupyter notebook cells.

    Runs code cells and captures their outputs, updating the notebook file
    with results. Requires jupyter_client to be installed.
    """

    @property
    def name(self) -> str:
        return "NotebookExecute"

    @property
    def description(self) -> str:
        return """Execute Jupyter notebook cells and capture outputs.

Runs code cells using a Jupyter kernel and updates the notebook with results.

IMPORTANT: Requires jupyter_client installed: pip install jupyter-client ipykernel

Examples:
- Execute cell 2: NotebookExecute(path="analysis.ipynb", cell_number=2)
- Execute all cells: NotebookExecute(path="analysis.ipynb", cell_number="all")
- Use specific kernel: NotebookExecute(path="analysis.ipynb", cell_number=2, kernel="python3")"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to .ipynb file",
                required=True,
            ),
            ToolParameter(
                name="cell_number",
                type=ToolParameterType.STRING,
                description="Cell index to execute (number) or 'all' for all code cells",
                required=True,
            ),
            ToolParameter(
                name="kernel",
                type=ToolParameterType.STRING,
                description="Kernel name (default: python3)",
                required=False,
            ),
            ToolParameter(
                name="timeout",
                type=ToolParameterType.NUMBER,
                description="Execution timeout in seconds (default: 30)",
                required=False,
            ),
        ]

    async def execute(
        self,
        path: str,
        cell_number: str,
        kernel: str = "python3",
        timeout: int = 30,
        **kwargs: Any
    ) -> ToolResult:
        """Execute notebook cell(s)."""
        try:
            # Check if jupyter_client is available
            try:
                from jupyter_client import KernelManager
            except ImportError:
                return ToolResult(
                    success=False,
                    output="",
                    error="jupyter_client not installed. Install with: pip install jupyter-client ipykernel"
                )

            # Expand path
            path = os.path.expanduser(path)

            # Check file exists
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Notebook not found: {path}"
                )

            # Load notebook
            with open(path, 'r') as f:
                notebook = json.load(f)

            cells = notebook.get('cells', [])

            # Determine which cells to execute
            if cell_number == "all":
                cells_to_execute = [
                    (i, cell) for i, cell in enumerate(cells)
                    if cell.get('cell_type') == 'code'
                ]
            else:
                try:
                    idx = int(cell_number)
                    if idx < 0 or idx >= len(cells):
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"Invalid cell_number {idx}. Notebook has {len(cells)} cells (0-{len(cells)-1})"
                        )

                    if cells[idx].get('cell_type') != 'code':
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"Cell {idx} is not a code cell (type: {cells[idx].get('cell_type')})"
                        )

                    cells_to_execute = [(idx, cells[idx])]
                except ValueError:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Invalid cell_number '{cell_number}'. Must be a number or 'all'"
                    )

            if not cells_to_execute:
                return ToolResult(
                    success=True,
                    output="No code cells to execute",
                    metadata={"cells_executed": 0}
                )

            # Start kernel
            km = KernelManager(kernel_name=kernel)
            km.start_kernel()
            kc = km.client()
            kc.start_channels()

            # Wait for kernel to be ready
            try:
                kc.wait_for_ready(timeout=timeout)
            except Exception as e:
                km.shutdown_kernel()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Kernel failed to start: {str(e)}"
                )

            execution_results = []

            # Execute cells
            for idx, cell in cells_to_execute:
                source = cell.get('source', [])
                if isinstance(source, list):
                    code = ''.join(source)
                else:
                    code = source

                # Skip empty cells
                if not code.strip():
                    execution_results.append(f"Cell {idx}: skipped (empty)")
                    continue

                # Execute code
                msg_id = kc.execute(code)

                # Collect outputs
                cell_outputs = []
                exec_count = None

                while True:
                    try:
                        msg = kc.get_iopub_msg(timeout=timeout)

                        if msg['parent_header'].get('msg_id') != msg_id:
                            continue

                        msg_type = msg['msg_type']
                        content = msg['content']

                        if msg_type == 'execute_input':
                            exec_count = content.get('execution_count')

                        elif msg_type == 'execute_result':
                            cell_outputs.append({
                                'output_type': 'execute_result',
                                'data': content['data'],
                                'execution_count': content['execution_count'],
                                'metadata': content.get('metadata', {})
                            })

                        elif msg_type == 'stream':
                            cell_outputs.append({
                                'output_type': 'stream',
                                'name': content['name'],
                                'text': content['text']
                            })

                        elif msg_type == 'display_data':
                            cell_outputs.append({
                                'output_type': 'display_data',
                                'data': content['data'],
                                'metadata': content.get('metadata', {})
                            })

                        elif msg_type == 'error':
                            cell_outputs.append({
                                'output_type': 'error',
                                'ename': content['ename'],
                                'evalue': content['evalue'],
                                'traceback': content['traceback']
                            })

                        elif msg_type == 'status' and content['execution_state'] == 'idle':
                            break

                    except Exception:
                        break

                # Update cell
                cells[idx]['outputs'] = cell_outputs
                cells[idx]['execution_count'] = exec_count

                # Report result
                output_count = len(cell_outputs)
                has_error = any(out.get('output_type') == 'error' for out in cell_outputs)
                status = "✗ error" if has_error else "✓ success"
                execution_results.append(f"Cell {idx}: {status} ({output_count} outputs)")

            # Cleanup kernel
            kc.stop_channels()
            km.shutdown_kernel()

            # Update notebook
            notebook['cells'] = cells

            # Save notebook
            with open(path, 'w') as f:
                json.dump(notebook, f, indent=1)

            return ToolResult(
                success=True,
                output="\n".join(execution_results),
                metadata={
                    "path": path,
                    "cells_executed": len(cells_to_execute),
                    "kernel": kernel
                }
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid JSON in notebook file: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to execute notebook: {str(e)}"
            )


class NotebookCreateTool(Tool):
    """Create a new Jupyter notebook.

    Creates a blank notebook or one with initial cells.
    """

    @property
    def name(self) -> str:
        return "NotebookCreate"

    @property
    def description(self) -> str:
        return """Create a new Jupyter notebook.

Creates an empty notebook or one with initial cells.

Examples:
- Empty notebook: NotebookCreate(path="new.ipynb")
- With initial cells: NotebookCreate(path="analysis.ipynb", initial_cells=[...])
- Specify kernel: NotebookCreate(path="analysis.ipynb", kernel="python3")"""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path for new .ipynb file",
                required=True,
            ),
            ToolParameter(
                name="kernel",
                type=ToolParameterType.STRING,
                description="Kernel name (default: python3)",
                required=False,
            ),
            ToolParameter(
                name="initial_cells",
                type=ToolParameterType.ARRAY,
                description="Optional array of initial cells: [{type: 'code'|'markdown', content: 'text'}]",
                required=False,
            ),
        ]

    async def execute(
        self,
        path: str,
        kernel: str = "python3",
        initial_cells: Optional[List[dict]] = None,
        **kwargs: Any
    ) -> ToolResult:
        """Create new notebook."""
        try:
            # Expand path
            path = os.path.expanduser(path)

            # Check if file already exists
            if os.path.exists(path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File already exists: {path}"
                )

            # Ensure .ipynb extension
            if not path.endswith('.ipynb'):
                path = path + '.ipynb'

            # Create cells
            cells = []

            if initial_cells:
                for cell_data in initial_cells:
                    cell_type = cell_data.get('type', 'code')
                    content = cell_data.get('content', '')

                    if cell_type not in ['code', 'markdown']:
                        return ToolResult(
                            success=False,
                            output="",
                            error=f"Invalid cell type '{cell_type}'. Must be 'code' or 'markdown'"
                        )

                    cell = {
                        'cell_type': cell_type,
                        'metadata': {},
                        'source': _format_source(content)
                    }

                    if cell_type == 'code':
                        cell['outputs'] = []
                        cell['execution_count'] = None

                    cells.append(cell)

            # Create notebook structure
            notebook = {
                'cells': cells,
                'metadata': {
                    'kernelspec': {
                        'display_name': f'Python 3' if kernel == 'python3' else kernel,
                        'language': 'python',
                        'name': kernel
                    },
                    'language_info': {
                        'name': 'python',
                        'version': '3.8.0'
                    }
                },
                'nbformat': 4,
                'nbformat_minor': 4
            }

            # Write notebook
            with open(path, 'w') as f:
                json.dump(notebook, f, indent=1)

            return ToolResult(
                success=True,
                output=f"Created notebook: {path}",
                metadata={
                    "path": path,
                    "cell_count": len(cells),
                    "kernel": kernel
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to create notebook: {str(e)}"
            )
