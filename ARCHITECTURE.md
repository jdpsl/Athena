# Athena Architecture

Complete documentation of Athena's multi-agent system architecture.

## Overview

Athena is an open-source AI agent system inspired by Claude Code, designed to work with any OpenAI-compatible API (LM Studio, ChatGPT, Groq, etc.). It features autonomous tool execution, multi-agent coordination, and thinking tag injection for models without native reasoning support.

## Core Components

### 1. Data Models (`athena/models/`)

**Message (`message.py`):**
- Represents conversation messages with roles (system, user, assistant, tool)
- Supports tool calls and tool results
- Includes thinking content for reasoning
- Converts to OpenAI API format

**Tool (`tool.py`):**
- Base class for all tools
- Defines parameter schema using Pydantic
- Executes with typed parameters
- Returns structured ToolResult

**Job (`job.py`):**
- Represents tasks in the queue
- States: pending → claimed → in_progress → completed/failed
- Supports parent-child relationships for sub-agents
- Tracks timing and retry logic

**Config (`config.py`):**
- LLMConfig: API endpoint, model, temperature
- AgentConfig: Max iterations, thinking settings
- ToolsConfig: Bash timeout, file size limits
- Loads from YAML or environment variables

### 2. LLM Client (`athena/llm/`)

**ThinkingInjector (`thinking_injector.py`):**
- Detects if model has native thinking support
- Injects `<thinking>` tag prompts for models without it
- Extracts and parses thinking content from responses
- Enforces thinking budget (token limits)

**LLMClient (`client.py`):**
- OpenAI-compatible API client
- Integrates thinking injection
- Supports streaming and non-streaming
- Handles tool calls in OpenAI format

### 3. Tool System (`athena/tools/`)

**ToolRegistry (`base.py`):**
- Manages all available tools
- Executes tools by name
- Converts tools to OpenAI function format

**File Operations (`file_ops.py`):**
- **Read**: Read files with line numbers (cat -n format)
- **Write**: Create/overwrite files
- **Edit**: Exact string replacement with validation

**Search Tools (`search.py`):**
- **Glob**: Pattern-based file finding (e.g., `**/*.py`)
- **Grep**: Regex content search with multiple output modes

**Bash Tool (`bash.py`):**
- Execute shell commands
- Configurable timeout (default 2min, max 10min)
- Output truncation at 30k chars
- Persistent working directory

**Todo Tool (`todo.py`):**
- Task list management
- Validates todo structure (content, status, activeForm)
- Enforces single in-progress task
- Tracks pending/in_progress/completed states

**Task Tool (`task.py`):**
- **Multi-agent orchestration**
- Spawns specialized sub-agents
- Waits for sub-agent completion
- Returns sub-agent report to parent

### 4. Agent System (`athena/agent/`)

**AgentType (`types.py`):**
- Defines specialized agent types:
  - `general-purpose`: Complex multi-step tasks
  - `Explore`: Codebase navigation and understanding
  - `Plan`: Task breakdown and planning
  - `code-reviewer`: Code quality and security review
  - `test-runner`: Test execution and analysis
- Each type has a specialized system prompt

**MainAgent (`main_agent.py`):**
- Coordinates task execution
- Manages conversation history
- Agent loop: generate → execute tools → repeat
- Supports parallel or sequential tool execution
- Enforces max iteration limits

**SubAgent (`sub_agent.py`):**
- Specialized agent spawned by Task tool
- Has own conversation context
- Uses specialized system prompt based on type
- Creates child jobs in queue
- Returns final report to parent

### 5. Job Queue (`athena/queue/`)

**SQLiteJobQueue (`sqlite_queue.py`):**
- SQLite-based task queue
- Atomic job claiming (prevents duplicate processing)
- Parent-child job relationships
- Status tracking with timestamps
- Priority-based ordering

**Job Flow:**
```
1. Main agent receives user request
2. Creates root job → PENDING
3. Worker claims job → CLAIMED
4. Agent processes → IN_PROGRESS
5. May spawn child jobs (sub-agents)
6. Completes → COMPLETED (or FAILED)
```

### 6. Hooks System (`athena/hooks/`)

**HookManager (`manager.py`):**
- Event-driven control over agent behavior
- Hook types:
  - `PRE_TOOL_USE`: Before tool execution
  - `POST_TOOL_USE`: After tool execution
  - `USER_PROMPT_SUBMIT`: When user submits prompt
  - `STOP`: When session ends
- Supports sync and async callbacks
- Can modify context data

### 7. Slash Commands (`athena/commands/`)

**CommandLoader (`loader.py`):**
- Loads commands from `.athena/commands/*.md`
- Expands slash commands in user input
- Supports command arguments
- Example: `/review` → expands to code review prompt

### 8. CLI Interface (`athena/cli.py`)

**AthenaSession:**
- Interactive REPL mode
- Single-task execution mode
- Rich terminal UI with markdown rendering
- Built-in commands: /help, /exit, /clear, /tools, etc.

**Initialization flow:**
```
1. Load configuration (YAML or env vars)
2. Initialize job queue (SQLite)
3. Register all tools
4. Create Task tool with queue reference
5. Initialize main agent
6. Load slash commands
7. Start REPL or execute single task
```

## Multi-Agent Architecture

### How Multi-Agent Works

```
User: "Explore how authentication works in this codebase"
  ↓
MainAgent receives task
  ↓
Decides to use Task tool
  ↓
TaskTool spawns SubAgent (type=Explore)
  ↓
SubAgent:
  - Gets specialized "Explore" system prompt
  - Has access to same tools (Read, Glob, Grep, etc.)
  - Creates child job in queue
  - Autonomously searches codebase
  - Reads relevant files
  - Builds understanding
  - Generates final report
  ↓
Report returned to MainAgent
  ↓
MainAgent continues with report info
```

### Agent Communication

- **Job Queue**: Parent-child relationships track agent hierarchy
- **Tool Results**: Sub-agent reports returned as tool results
- **Context Isolation**: Each agent has own conversation history
- **Tool Sharing**: All agents share the same tool registry

### When to Use Sub-Agents

The Task tool is useful for:
1. **Complex exploration** - "Find all API endpoints"
2. **Planning** - "Design architecture for new feature"
3. **Code review** - "Review this PR for security issues"
4. **Autonomous tasks** - "Fix all linting errors"

## Thinking Tag Injection

### Problem
Most open-source models (Llama, Mistral, etc.) don't have native thinking/reasoning capabilities like Claude.

### Solution
Athena injects thinking support:

**Detection:**
```python
# Check if model needs injection
if "claude" in model_name or "deepseek-r1" in model_name:
    use_native = True  # Has native thinking
else:
    inject_thinking = True  # Needs injection
```

**Injection:**
```python
# Add system prompt
system_msg = """
Use <thinking> tags for reasoning:
<thinking>
Step 1: Analyze the problem
Step 2: Consider approaches
Step 3: Plan solution
</thinking>

Then provide your response.
"""
```

**Extraction:**
```python
# Parse response
thinking = extract_between("<thinking>", "</thinking>")
response = remove_thinking_tags(full_response)
```

### Benefits
- Makes any model reason explicitly
- Improves code quality
- Better debugging (can see reasoning)
- Consistent behavior across models

## Example Workflows

### 1. Simple Task (No Sub-Agents)
```
User: "Create a hello world script"
→ MainAgent uses Write tool
→ Returns result
```

### 2. Complex Exploration (Uses Sub-Agent)
```
User: "How does the auth system work?"
→ MainAgent spawns Explore sub-agent
→ SubAgent:
    - Globs for auth files
    - Greps for auth patterns
    - Reads relevant code
    - Analyzes architecture
    - Returns comprehensive report
→ MainAgent synthesizes findings
→ Returns explanation to user
```

### 3. Multi-Step with Planning
```
User: "Add rate limiting to the API"
→ MainAgent spawns Plan sub-agent
→ Plan agent:
    - Reads existing API code
    - Designs rate limiting approach
    - Creates step-by-step plan
    - Returns plan
→ MainAgent executes plan steps:
    - Read middleware file
    - Edit to add rate limiter
    - Write tests
    - Run tests via Bash
→ Returns completed task
```

## Key Design Decisions

### 1. SQLite for Job Queue
**Why:** Simple, serverless, no external dependencies
**Trade-off:** Not suitable for distributed systems (use Redis for that)

### 2. OpenAI Protocol
**Why:** Maximum compatibility with existing tools
**Benefit:** Works with LM Studio, vLLM, OpenAI, Groq, Together, etc.

### 3. Thinking Injection
**Why:** Most open models lack reasoning capabilities
**Impact:** Dramatically improves output quality for planning tasks

### 4. Tool-First Design
**Why:** Tools are the agent's "hands" in the world
**Result:** Easy to extend with new capabilities

### 5. Async Throughout
**Why:** Efficient I/O handling, supports parallel operations
**Benefit:** Can run multiple sub-agents or tools concurrently

## Extending Athena

### Adding a New Tool
```python
from athena.models.tool import Tool, ToolParameter, ToolResult

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "MyTool"

    @property
    def description(self) -> str:
        return "What it does"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [...]

    async def execute(self, **kwargs) -> ToolResult:
        # Implementation
        return ToolResult(success=True, output="result")
```

### Adding a New Agent Type
```python
# In athena/agent/types.py
class AgentType(str, Enum):
    # ...existing types...
    MY_AGENT = "my-agent"

AGENT_SYSTEM_PROMPTS[AgentType.MY_AGENT] = """
Specialized system prompt for this agent type...
"""
```

### Adding a Hook
```python
from athena.hooks import HookManager, HookType

async def my_hook(context):
    print(f"Tool being called: {context['tool_name']}")
    # Can modify context or block execution
    return context

hook_manager.register(HookType.PRE_TOOL_USE, my_hook)
```

## Comparison with Claude Code

| Feature | Athena | Claude Code |
|---------|--------|-------------|
| Multi-agent | ✅ 5 agent types | ✅ Multiple agents |
| Thinking injection | ✅ For any model | ✅ Native support |
| Tools | ✅ 8 core tools | ✅ ~18 tools |
| Job queue | ✅ SQLite | ✅ Internal |
| Hooks | ✅ Basic | ✅ Advanced |
| Open source | ✅ Yes | ❌ No |
| Model support | ✅ Any OpenAI-compatible | ❌ Claude only |
| Cost | ✅ Free (local) or cheap | 💰 Claude API pricing |

## Performance Considerations

**Token Usage:**
- Thinking injection adds ~200 tokens to system prompt
- Each tool call adds ~100-500 tokens
- Sub-agents have separate contexts (don't pollute main context)

**Speed:**
- Local models (LM Studio): 10-50 tokens/sec
- Groq: 200-500 tokens/sec (very fast!)
- OpenAI: 50-100 tokens/sec

**Concurrency:**
- Parallel tool calls: 2-3x faster for independent operations
- Sub-agents can run in parallel (future enhancement)

## Future Enhancements

1. **Streaming responses** - Show output as it's generated
2. **Web tools** - WebFetch, WebSearch integration
3. **MCP support** - Model Context Protocol for external integrations
4. **Parallel sub-agents** - Multiple agents working simultaneously
5. **Context compression** - Smart history management for long sessions
6. **Docker sandboxing** - Safe code execution
7. **Resume sessions** - Save and restore conversations
8. **Plugin system** - Easy third-party tool integration

## Conclusion

Athena provides a complete, production-ready AI agent system with:
- ✅ Multi-agent orchestration
- ✅ Autonomous tool execution
- ✅ Thinking injection for any model
- ✅ OpenAI compatibility
- ✅ Clean, extensible architecture

Perfect for building AI coding assistants, automation tools, or custom agent workflows!
