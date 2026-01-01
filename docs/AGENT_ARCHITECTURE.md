# Athena Agent Architecture

**Last Updated:** 2025-12-28

## Overview

Athena uses a unified agent architecture based on `BaseAgent`, which provides automatic context compression and selective tool registration. This architecture eliminates code duplication and enables specialized agents with minimal overhead.

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│              BaseAgent                      │
│  - Unified agent loop                       │
│  - Context compression (auto)               │
│  - Tool filtering                           │
│  - Message management                       │
│  - Streaming support                        │
└─────────────┬───────────────────────────────┘
              │
      ┌───────┴────────┬─────────┬──────────┬───────────┐
      ▼                ▼         ▼          ▼           ▼
┌──────────┐   ┌──────────┐  ┌──────┐  ┌──────────┐  ┌───────────┐
│MainAgent │   │ Explore  │  │ Plan │  │CodeReview│  │TestRunner │
│(all tools)   │(3 tools) │  │Agent │  │  Agent   │  │  Agent    │
└──────────┘   └──────────┘  └──────┘  └──────────┘  └───────────┘
```

## Core Components

### BaseAgent (`athena/agent/base_agent.py`)

The abstract base class that all agents inherit from. Provides:

- **Unified Agent Loop:** Single implementation of the request-response cycle
- **Context Management:** Automatic tracking and compression of conversation history
- **Tool Filtering:** Selective tool registration based on agent specialization
- **Streaming Support:** Real-time response streaming to the user
- **Error Handling:** Fallback parsing for non-standard tool calls

**Key Methods:**

```python
class BaseAgent(ABC):
    @abstractmethod
    def get_agent_type_name(self) -> str:
        """Return agent type identifier."""
        pass

    @abstractmethod
    def get_allowed_tools(self) -> Optional[list[str]]:
        """Return list of allowed tool names, or None for all tools."""
        pass

    async def run(self, user_message: str, job_type: str = "task") -> str:
        """Main entry point for agent execution."""
        pass

    async def _agent_loop(self) -> str:
        """Core agent loop with context compression."""
        pass
```

### MainAgent (`athena/agent/main_agent.py`)

The primary agent with access to all tools. Used for interactive sessions and general-purpose tasks.

**Configuration:**
- Tools: All registered tools (22 tools)
- Type: `main`

**Usage:** Default agent for CLI sessions

### Specialized Agents (`athena/agent/specialized.py`)

#### ExploreAgent
Fast exploration and search agent.

**Configuration:**
- Tools: `Glob`, `Grep`, `Read` (3 tools)
- Type: `explore`
- Token Savings: ~140 tokens per call (57.1% reduction)

**Use Cases:**
- Codebase exploration
- Finding files and patterns
- Reading source code

#### PlanAgent
Planning and task breakdown agent.

**Configuration:**
- Tools: `Glob`, `Grep`, `Read`, `TodoWrite` (4 tools)
- Type: `plan`
- Token Savings: ~105 tokens per call (42.9% reduction)

**Use Cases:**
- Implementation planning
- Task decomposition
- Architecture design

#### CodeReviewAgent
Code review and analysis agent.

**Configuration:**
- Tools: `Read`, `Grep`, `Glob`, `TodoWrite` (4 tools)
- Type: `code-reviewer`
- Token Savings: ~105 tokens per call (42.9% reduction)

**Use Cases:**
- Code reviews
- Finding bugs
- Suggesting improvements

#### TestRunnerAgent
Test execution and verification agent.

**Configuration:**
- Tools: `Read`, `Grep`, `Glob`, `Bash` (4 tools)
- Type: `test-runner`
- Token Savings: ~105 tokens per call (42.9% reduction)

**Use Cases:**
- Running test suites
- Executing commands
- Build verification

## Context Management

### ContextManager (`athena/context/manager.py`)

Tracks token usage and triggers compression.

**Configuration:**
- Max Tokens: 8000
- Compression Threshold: 75% (6000 tokens)
- Token Estimation: 1 token ≈ 4 characters

**Features:**
- Real-time token estimation
- Automatic compression triggering
- Statistics tracking

### MessageCompressor (`athena/context/compressor.py`)

Compresses conversation history by summarizing old messages.

**Strategy:**
1. Keep system message (if present)
2. Summarize middle messages
3. Keep last N recent messages (default: 10)

**Example:**
- Before: 60 messages (~8000 tokens)
- After: 11 messages (~2000 tokens)
- Reduction: 75%

## Task Tool Integration

The `TaskTool` spawns specialized agents based on task requirements.

**Agent Selection:**
```python
agent_map = {
    AgentType.EXPLORE: ExploreAgent,       # Fast search
    AgentType.PLAN: PlanAgent,             # Planning
    AgentType.CODE_REVIEWER: CodeReviewAgent,  # Reviews
    AgentType.TEST_RUNNER: TestRunnerAgent,    # Testing
    AgentType.GENERAL: SubAgent,           # Fallback
}
```

**Note:** Specialized agents use lazy imports to avoid circular dependencies.

## Performance Metrics

### Token Savings

| Agent | Tools | Tokens | Savings |
|-------|-------|--------|---------|
| MainAgent | 7 | ~245 | 0% (baseline) |
| ExploreAgent | 3 | ~105 | 57.1% |
| PlanAgent | 4 | ~140 | 42.9% |
| CodeReviewAgent | 4 | ~140 | 42.9% |
| TestRunnerAgent | 4 | ~140 | 42.9% |

### Code Reduction

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| MainAgent | 250 LOC | 24 LOC | 90% |
| Total Agent Code | 440 LOC | 406 LOC | Eliminated duplication |

### Context Compression

- **Trigger Point:** 6000 tokens (75% of max)
- **Compression Ratio:** ~75% reduction
- **Recent Messages Kept:** 10
- **Impact:** Prevents context overflow in long sessions

## Implementation Details

### Creating a New Specialized Agent

1. **Extend BaseAgent:**
```python
from athena.agent.base_agent import BaseAgent

class MySpecializedAgent(BaseAgent):
    def get_agent_type_name(self) -> str:
        return "my-agent"

    def get_allowed_tools(self) -> Optional[list[str]]:
        return ["Tool1", "Tool2", "Tool3"]
```

2. **Register in AgentType:**
```python
# In athena/agent/types.py
class AgentType(str, Enum):
    MY_AGENT = "my-agent"
```

3. **Add to TaskTool:**
```python
# In athena/tools/task.py
agent_map = {
    # ... existing mappings ...
    AgentType.MY_AGENT: MySpecializedAgent,
}
```

4. **Create System Prompt:**
```python
# In athena/agent/types.py
def get_system_prompt(agent_type: AgentType) -> str:
    if agent_type == AgentType.MY_AGENT:
        return "You are a specialized agent for..."
```

### Avoiding Circular Imports

**Problem:** Agents import tools, tools import agents → circular dependency

**Solution:** Lazy imports in TaskTool
```python
# In athena/tools/task.py
async def execute(self, ...):
    # Import inside method, not at module level
    from athena.agent.specialized import ExploreAgent, PlanAgent
    # ... use agents ...
```

## Testing

### Test Files

1. **`test_context_management.py`**
   - Context manager token estimation
   - Compression triggering
   - Message compression logic

2. **`test_base_agent_architecture.py`**
   - Tool filtering per agent
   - Agent type names
   - Context compression integration
   - Token savings calculations

### Running Tests

```bash
# Test context management
python3 test_context_management.py

# Test agent architecture
python3 test_base_agent_architecture.py
```

**Expected Results:** All tests pass ✅

## Migration Notes

### From Old Architecture

**Before:**
- Separate MainAgent and SubAgent classes
- Duplicated agent loop code
- No context compression
- All tools sent to LLM

**After:**
- Unified BaseAgent with specializations
- Single agent loop implementation
- Automatic context compression
- Selective tool registration

### Breaking Changes

None. The new architecture is backward compatible. Old code using `MainAgent` continues to work.

### Deprecated

- `MainAgent._agent_loop()` - Now inherited from BaseAgent
- `SubAgent._agent_loop()` - Now inherited from BaseAgent

Files kept for reference:
- `athena/agent/main_agent_old.py` (original MainAgent)
- `athena/agent/sub_agent.py` (original SubAgent)

## Future Enhancements

### Planned Features

1. **SQLite Job Queue Integration**
   - Persistent agent state
   - Resume from checkpoints
   - Job tracking and history

2. **Advanced Context Strategies**
   - Semantic compression (keep important messages)
   - Multi-tier summarization
   - Topic-based organization

3. **Agent Chaining**
   - Automatically spawn specialized agents
   - Pipeline multiple agents
   - Parallel agent execution

4. **Performance Optimizations**
   - Tool definition caching
   - Parallel tool execution
   - Faster token estimation

## References

- **BaseAgent:** `athena/agent/base_agent.py`
- **Specialized Agents:** `athena/agent/specialized.py`
- **Context Management:** `athena/context/`
- **Task Tool:** `athena/tools/task.py`
- **Tests:** `test_base_agent_architecture.py`
- **Refactoring Plan:** `REFACTORING_PLAN.md`
- **Backup:** `.backup/athena_20251228_120714/`
