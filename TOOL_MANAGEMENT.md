# Tool Management System

## Overview

Athena now features an automatic tool discovery and management system that eliminates the need for manual tool registration. Tools are automatically discovered from the `athena/tools/` directory and can be enabled/disabled on the fly.

## Features

### 1. **Auto-Discovery**
- Tools are automatically discovered and loaded from `athena/tools/` directory
- No need to manually import and register tools in `cli.py`
- Just drop a new tool file in `athena/tools/` and it will be available immediately

### 2. **Enable/Disable Tools**
- Disable tools you don't need to reduce clutter
- Enable/disable persists across sessions (saved to `~/.athena/config.json`)
- Changes take effect immediately

### 3. **Tool Inspection**
- View detailed information about any tool
- See parameters, descriptions, and enabled status
- Easy to understand what each tool does

## Usage

### List All Tools
```bash
/tools
```
Shows all available tools with their status (● enabled, ○ disabled)

Example output:
```
Available Tools:
  ● Read: Reads a file from the filesystem
  ● Write: Writes content to a file
  ○ WebSearch: Search the web (disabled)
  ● Bash: Execute bash commands
  ...

Total: 28 tools enabled
Use /tool <name> to see details or /tool <name> on/off to enable/disable
```

### View Tool Details
```bash
/tool Read
```
Shows detailed information about a specific tool including:
- Description
- Parameters (name, type, required/optional, description)
- Current status (enabled/disabled)

Example output:
```
Read - enabled

Reads a file from the filesystem. Returns content with line numbers.

Parameters:
  • file_path (string) *
    The absolute path to the file to read
  • offset (number) (optional)
    Line number to start reading from
  • limit (number) (optional)
    Number of lines to read

Use /tool Read on/off to enable/disable
```

### Disable a Tool
```bash
/tool WebSearch off
```
Disables the WebSearch tool. It will no longer appear in the tool list sent to the LLM.

### Enable a Tool
```bash
/tool WebSearch on
```
Re-enables a previously disabled tool.

### Save Configuration
```bash
/save
```
Saves your tool preferences (along with other settings) to `~/.athena/config.json`. These settings are automatically loaded on startup.

Example output:
```
✓ Settings saved to ~/.athena/config.json
  Model: gpt-4
  API Base: https://api.openai.com/v1
  Temperature: 0.7
  Context Size: 8000 tokens (compresses at 75%)
  Interaction Mode: collaborative
  MCP Servers: 2 saved
  Disabled Tools: 3 disabled
```

## How It Works

### Auto-Discovery Process

1. **Scan**: On startup, Athena scans `athena/tools/` for `.py` files
2. **Import**: Each module is dynamically imported
3. **Discover**: Classes that inherit from `Tool` are identified
4. **Instantiate**: Tools with no required constructor parameters are automatically instantiated
5. **Register**: Instantiated tools are registered in the `ToolRegistry`
6. **Filter**: Disabled tools (from config) are excluded

### Special Tools

Some tools require special initialization and are handled separately:
- **Bash**: Needs timeout configuration from settings
- **WebFetch**: Gets LLM client reference after agent initialization
- **Task**: Requires job queue reference

These tools are still registered automatically but with custom initialization logic.

### Persistence

Tool enable/disable state is stored in `~/.athena/config.json`:

```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "disabled_tools": ["WebSearch", "WebFetch", "GitPush"],
  ...
}
```

## Benefits

### For Users
- **Cleaner tool list**: Disable tools you never use
- **Faster responses**: Fewer tools means smaller context for the LLM
- **Better control**: Choose exactly which capabilities Athena has
- **Easy discovery**: See what tools are available and what they do

### For Developers
- **No manual registration**: Just create a tool class, save the file, done!
- **Automatic updates**: New tools are immediately available
- **Clean codebase**: No need to maintain import lists in `cli.py`
- **Easy testing**: Create test tools without modifying core files

## Example Workflow

```bash
# Start Athena
python3 -m athena

# See what tools are available
/tools

# I don't need git push, disable it
/tool GitPush off

# Save this preference
/save

# Later, check what MathTool does
/tool Math

# Output:
# Math - enabled
#
# Evaluate mathematical expressions accurately using Python's math library
#
# Parameters:
#   • expression (string) *
#     The mathematical expression to evaluate
```

## Adding New Tools

To add a new tool:

1. Create a new file in `athena/tools/` (e.g., `my_tool.py`)
2. Define a class that inherits from `Tool`:

```python
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult

class MyAwesomeTool(Tool):
    @property
    def name(self) -> str:
        return "MyAwesome"

    @property
    def description(self) -> str:
        return "Does something awesome"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type=ToolParameterType.STRING,
                description="Input to process",
                required=True,
            )
        ]

    async def execute(self, input: str, **kwargs) -> ToolResult:
        # Your tool logic here
        return ToolResult(
            success=True,
            output=f"Processed: {input}"
        )
```

3. That's it! The tool will automatically appear in `/tools` on next startup

## Technical Details

### ToolRegistry Methods

- `auto_discover_tools(disabled_tools)` - Scan and register tools from tools directory
- `enable_tool(tool_name)` - Enable a disabled tool
- `disable_tool(tool_name)` - Disable an enabled tool
- `is_tool_enabled(tool_name)` - Check if tool is enabled
- `get_tool_info(tool_name)` - Get detailed info about a tool

### Files Modified

- `athena/tools/base.py` - Added auto-discovery and enable/disable methods
- `athena/config_manager.py` - Added disabled_tools persistence
- `athena/cli.py` - Added `/tool` command and auto-discovery integration

## Discovered Tools (Current)

As of the last scan, Athena discovered **28 tools**:

File Operations:
- Read, Write, Edit, Insert
- DeleteFile, MoveFile, CopyFile
- ListDir, MakeDir

Search:
- Glob, Grep

Execution:
- Bash

Git:
- GitStatus, GitDiff, GitCommit, GitLog, GitBranch, GitPush, GitCreatePR

Web:
- WebSearch, WebFetch

Notebooks:
- NotebookRead, NotebookEdit, NotebookExecute, NotebookCreate

Utility:
- Math, TodoWrite, AskUserQuestion

Special (manually registered):
- Task (requires job queue)

## Future Enhancements

Possible future improvements:
- Tool categories/groups for better organization
- Search/filter tools by name or category
- Tool usage statistics
- Recommended tool sets for different workflows
- Tool dependencies and conflicts
- Custom tool directories (project-specific tools)
