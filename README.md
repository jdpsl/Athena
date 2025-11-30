# Athena

Open-source AI agent system for autonomous coding assistance, inspired by Claude Code.

## Features

- **Multi-agent architecture** - Spawn specialized agents for different tasks (Explore, Plan, code-reviewer, test-runner)
- **Comprehensive tool system** - 21 tools including file operations, Git, web access, and more
- **Fallback mode** - Works with ANY model, even without function calling support
- **Thinking tag injection** - Add reasoning capabilities to models that lack native thinking
- **OpenAI protocol compatible** - Works with LM Studio, ChatGPT, Groq, Ollama, and more
- **Persistent configuration** - Save your settings to `~/.athena/config.json`
- **Job queue system** - Efficient task management and execution
- **Hooks** - Event-driven control over agent behavior
- **Slash commands** - Custom user-defined commands
- **Web access** - Search the internet and fetch web pages
- **Interactive questions** - Agent can ask you for clarification

## Installation

### Requirements
- Python 3.10 or higher
- An OpenAI-compatible API (LM Studio, OpenAI, Groq, etc.)

### Install
```bash
cd athena
pip install -e .
```

## Quick Start

### 1. Start Athena
```bash
athena
```

### 2. Configure on First Run
```bash
# Set your API endpoint
/api http://localhost:1234/v1

# Set API key (if needed)
/apikey sk-your-key-here

# For local models without function calling support
/fallback on

# Save settings for next time
/save
```

### 3. Start Coding
```
You: Read main.py and explain what it does
You: Create a Python script that processes CSV files
You: Search for all TODO comments in this project
```

## Configuration

### Option 1: Interactive Configuration (Recommended)
Start Athena and use commands:
- `/api <url>` - Set API base URL
- `/apikey <key>` - Set API key
- `/model <name>` - Set model name
- `/temp <0.0-1.0>` - Set temperature
- `/fallback on/off` - Toggle fallback mode
- `/save` - Save settings to `~/.athena/config.json`

Settings are automatically loaded on next startup!

### Option 2: Config File
Create `config.yaml` in your project directory:

```yaml
llm:
  api_base: "http://localhost:1234/v1"
  api_key: "not-needed-for-local"
  model: "local-model"
  temperature: 0.7

agent:
  max_iterations: 50
  enable_thinking: true
  fallback_mode: false  # Enable for models without function calling
  parallel_tool_calls: true

tools:
  bash_timeout: 120000
  max_file_size: 10000000
```

### Option 3: Environment Variables
Create `.env` file:
```env
ATHENA_API_BASE=http://localhost:1234/v1
ATHENA_API_KEY=not-needed-for-local
ATHENA_MODEL=local-model
ATHENA_TEMPERATURE=0.7
ATHENA_MAX_ITERATIONS=50
ATHENA_ENABLE_THINKING=true
```

## Fallback Mode (Important!)

Many local models don't support OpenAI-style function calling. If you get JSON parsing errors, enable fallback mode:

```bash
/fallback on
```

**What it does:**
- Uses text-based tool calling: `TOOL[Name]{"param": "value"}`
- Works with ANY model that can follow instructions
- No need for native function calling support
- Automatically teaches the model the format

**When to use:**
- ✅ Local models in LM Studio (Llama, Mistral, etc.)
- ✅ Models without function calling training
- ✅ Getting "invalid JSON" errors from the API
- ❌ OpenAI GPT-4/GPT-3.5 (they have native support)
- ❌ Models specifically trained for function calling (Hermes, Functionary)

## Available Tools

### File Operations (8 tools)
- **Read** - Read files with line numbers and syntax highlighting
- **Write** - Create or overwrite files
- **Edit** - Make precise edits with string replacement
- **DeleteFile** - Delete files or directories (with safety checks)
- **MoveFile** - Move or rename files
- **CopyFile** - Copy files or directories
- **ListDir** - List directory contents with sizes
- **MakeDir** - Create directories

### Search (2 tools)
- **Glob** - Find files by pattern (e.g., `**/*.py`, `src/**/*.tsx`)
- **Grep** - Search file contents with regex, supports context lines

### Git Version Control (5 tools)
- **GitStatus** - Check repository status, staged/modified files
- **GitDiff** - View diffs (staged or unstaged)
- **GitCommit** - Create commits (must stage files first with Bash)
- **GitLog** - View commit history
- **GitBranch** - List, create, switch, or delete branches

### Execution
- **Bash** - Execute shell commands with timeout and output capture

### Web Access (2 tools)
- **WebSearch** - Search the internet (DuckDuckGo, Brave, Google, SearXNG)
- **WebFetch** - Fetch and read web pages (HTML→Markdown conversion, AI extraction)

### Task Management
- **TodoWrite** - Track progress on multi-step tasks

### Agent Spawning
- **Task** - Spawn specialized sub-agents:
  - `Explore` - Navigate and understand codebases
  - `Plan` - Break down complex tasks
  - `code-reviewer` - Review code quality
  - `test-runner` - Run and analyze tests
  - `general-purpose` - Handle complex multi-step work

### User Interaction
- **AskUserQuestion** - Ask clarifying questions during execution

## Built-in Commands

### Configuration
- `/help` - Show all commands
- `/config` - Show current configuration
- `/model [name]` - Show or set model
- `/api [url]` - Show or set API base URL
- `/apikey [key]` - Show or set API key (masked when showing)
- `/temp [0.0-1.0]` - Show or set temperature
- `/fallback [on|off]` - Toggle text-based tool calling
- `/save` - Save settings to `~/.athena/config.json`

### Session Management
- `/clear` - Clear conversation history
- `/exit` or `/quit` - Exit Athena

### Information
- `/tools` - List all available tools
- `/commands` - List custom slash commands

## Custom Slash Commands

Create `.athena/commands/review.md`:
```markdown
Review the code for:
- Security vulnerabilities (SQL injection, XSS, etc.)
- Performance issues
- Code quality and best practices
- Potential bugs
```

Use it:
```
You: /review
```

Example commands included:
- `/review` - Code review
- `/explain` - Explain code
- `/test` - Generate tests
- `/debug` - Debug assistance
- `/optimize` - Performance optimization
- `/document` - Generate documentation
- `/refactor` - Refactoring suggestions

## Usage Examples

### File Operations
```
You: Read app.py and explain what it does
You: Create a new file called utils.py with helper functions
You: Move old_file.py to archive/old_file.py
You: Delete all .pyc files in this directory
```

### Git Operations
```
You: Check git status
You: Show me the diff of my changes
You: Create a commit with message "Add new feature"
You: Switch to a new branch called feature-x
```

### Web Research
```
You: Search the web for "Python async best practices"
You: Fetch the documentation from https://docs.python.org/3/library/asyncio.html
```

### Multi-Agent Tasks
```
You: Explore the codebase and find where authentication is handled
You: Review the code in auth.py for security issues
```

## Architecture

### Agent System
- **MainAgent** - Coordinates work, executes tools, manages conversation
- **SubAgents** - Specialized agents for complex tasks (Explore, Plan, etc.)
- Agents communicate via job queue with parent-child relationships

### Tool System
- Modular design with base `Tool` class
- Tools convert to OpenAI function format
- Registry pattern for dynamic tool loading
- Async execution with parallel support

### Job Queue
- SQLite-based persistent queue
- Track task status (pending, in_progress, completed, failed)
- Support for parent-child job relationships
- Enables agent coordination and sub-task spawning

### Thinking Injection
- Automatically adds `<thinking>` tags to models without native reasoning
- Extracts and displays thinking separately from responses
- Configurable token budget for thinking content
- Works with any OpenAI-compatible model

### Fallback Parser
- Regex-based tool call extraction from text
- Supports `TOOL[Name]{json}` format
- Handles malformed JSON with key:value parsing
- Automatic instruction injection into system prompt

## Tips & Best Practices

### For Best Results
1. **Enable fallback mode** if using local models without function calling
2. **Use lower temperature** (0.3-0.5) for more reliable tool usage
3. **Let Athena read files** before editing for better accuracy
4. **Use `/clear`** periodically to reduce context size
5. **Save your config** with `/save` to avoid reconfiguring

### Recommended Models

**With Native Function Calling:**
- OpenAI GPT-4, GPT-3.5
- Hermes-2-Pro, Hermes-3
- Functionary models
- Mistral-NeMo-Instruct

**With Fallback Mode:**
- Any Llama model (3, 3.1, 3.2)
- Mistral base models
- Qwen models
- Most local models in LM Studio

### Performance Tips
- Use smaller models (7B-13B) for faster responses
- Enable `parallel_tool_calls` for multi-tool operations
- Increase `bash_timeout` for long-running commands
- Use `/fallback on` to reduce API overhead

## Troubleshooting

### "Invalid JSON" / "400 Error: invalid request content"
**Solution:** Enable fallback mode
```bash
/fallback on
```
This means your model doesn't support function calling natively.

### "Connection refused" error
- Ensure LM Studio (or your API) is running
- Check the port matches: `/api http://localhost:1234/v1`
- Verify the API is accessible: `curl http://localhost:1234/v1/models`

### Model not responding
- Check if model is loaded in LM Studio
- Try lower temperature: `/temp 0.3`
- Increase max_tokens in config if responses are cut off

### "Python version not compatible"
- Athena requires Python 3.10+
- Check version: `python3 --version`
- Install Python 3.10+: `brew install python@3.11` (macOS)

### Slow responses
- Use a smaller model (7B instead of 70B)
- Clear context: `/clear`
- Consider faster providers (Groq, OpenAI)
- Enable parallel tool calls in config

## Development

### Setup Development Environment
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black athena/
ruff check athena/
```

### Creating New Tools
```python
from athena.models.tool import Tool, ToolParameter, ToolParameterType, ToolResult

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "MyTool"

    @property
    def description(self) -> str:
        return "Description of what my tool does"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="param1",
                type=ToolParameterType.STRING,
                description="Parameter description",
                required=True,
            )
        ]

    async def execute(self, param1: str, **kwargs) -> ToolResult:
        # Tool implementation
        return ToolResult(
            success=True,
            output="Result of the operation",
        )
```

Register in `athena/cli.py`:
```python
from athena.tools.my_tool import MyTool

# In _register_tools method:
self.tool_registry.register(MyTool())
```

## Contributing

Contributions welcome! Areas of interest:
- New tools (database access, API calls, code analysis)
- Improved fallback parsing
- Better error handling
- Documentation and examples
- Performance optimizations

## License

MIT License - see LICENSE file

## Credits

Inspired by [Claude Code](https://claude.com/claude-code) by Anthropic.

Built with:
- OpenAI Python SDK
- Pydantic for data validation
- Rich for beautiful terminal output
- Click for CLI
- Trafilatura for web content extraction
