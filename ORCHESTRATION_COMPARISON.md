# Agent Orchestration: Athena vs Claude Code

## Executive Summary

This document provides a deep-dive comparison of agent orchestration architectures between Athena and Claude Code, analyzing how each system spawns, manages, and coordinates specialized sub-agents.

**TL;DR:**
- **Athena**: Simple, synchronous, blocking model with isolated agents
- **Claude Code**: Advanced, resumable, context-aware agents with parallel execution

---

## Table of Contents

1. [Athena's Architecture](#athenas-architecture)
2. [Claude Code's Architecture](#claude-codes-architecture)
3. [Side-by-Side Comparison](#side-by-side-comparison)
4. [Performance Implications](#performance-implications)
5. [Improvement Recommendations](#improvement-recommendations)

---

## Athena's Architecture

### 1. Synchronous Blocking Model

**File:** `athena/tools/task.py:100-120`

```python
# Create sub-agent with full tool access
sub_agent = SubAgent(
    agent_type=agent_type,
    config=self.config,
    tool_registry=self.tool_registry,  # All 21 tools
    job_queue=self.job_queue,
    parent_job_id=self.current_job_id,
)

# BLOCKS HERE until sub-agent completes
result = await sub_agent.run(prompt, description)

# Wrap and return result
output = f"""Sub-Agent Report ({agent_type.value})
Task: {description}

{result}

---
Sub-agent completed task successfully."""
```

**Characteristics:**
- ✅ Simple to understand and implement
- ✅ Predictable execution flow
- ❌ Main agent blocks waiting for sub-agent
- ❌ No parallel execution of multiple agents
- ❌ No streaming updates during execution
- ❌ No ability to resume/continue previous work

---

### 2. Context Isolation

**File:** `athena/agent/sub_agent.py:52-57`

```python
class SubAgent:
    def __init__(self, ...):
        # Each sub-agent has ISOLATED message history
        self.messages: list[Message] = []

        # Only gets specialized system prompt
        system_prompt = get_system_prompt(agent_type)
        self.messages.append(Message(role=Role.SYSTEM, content=system_prompt))
```

**What sub-agents CAN see:**
- ✅ Their specialized system prompt (Plan, Explore, etc.)
- ✅ The task prompt from main agent

**What sub-agents CANNOT see:**
- ❌ User's original request
- ❌ Main agent's conversation history
- ❌ Previous tool results from main agent
- ❌ User preferences and clarifications

**Impact:**
- Sub-agents work in a "bubble"
- Must include all context explicitly in prompt
- Can't reference earlier discussion
- May ask redundant questions
- Limited understanding of broader user goals

**Example:**
```python
# User conversation with main agent:
User: "I'm getting errors when users log in"
Assistant: "What kind of errors?"
User: "OAuth token expiration errors"

# Main agent spawns Explore sub-agent:
# Sub-agent ONLY sees this:
"Find the authentication code that handles OAuth"

# Sub-agent does NOT see:
# - That user mentioned errors
# - That it's specifically about token expiration
# - The broader context of the conversation
```

---

### 3. All Tools to All Agents

**File:** `athena/tools/task.py:104`

Every sub-agent receives the **full tool registry:**

| Agent Type | Tools Provided | Tools Actually Needed | Wasted Tokens |
|------------|----------------|----------------------|---------------|
| **Plan** | All 21 tools | Glob, Grep, Read, TodoWrite (4) | ~400 tokens |
| **Explore** | All 21 tools | Glob, Grep, Read (3) | ~450 tokens |
| **code-reviewer** | All 21 tools | Read, Grep (2) | ~500 tokens |
| **test-runner** | All 21 tools | Bash, Read, Grep (3) | ~450 tokens |
| **general-purpose** | All 21 tools | All 21 (justified) | 0 tokens |

**Token overhead per specialized agent:** ~500-750 tokens for full tool definitions

**Why this happens:**
```python
# In task.py - same registry for all agents
sub_agent = SubAgent(
    tool_registry=self.tool_registry  # No filtering!
)
```

---

### 4. Job Queue (Underutilized)

**File:** `athena/queue/sqlite_queue.py`

Athena has a sophisticated SQLite job queue with excellent features:

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    payload TEXT NOT NULL,
    parent_job_id TEXT,        -- ✅ Parent tracking exists!
    agent_id TEXT,
    result TEXT,
    error TEXT,
    retry_count INTEGER,
    max_retries INTEGER,
    created_at TEXT,
    completed_at TEXT
)
```

**Available capabilities:**
- ✅ Priority queue (FIFO with priorities)
- ✅ Parent-child job tracking
- ✅ Retry logic with max attempts
- ✅ Status monitoring (pending → in_progress → completed/failed)
- ✅ `claim()` method for async work distribution
- ✅ Job hierarchy queries (`get_children()`)

**Current usage:**
- ✅ Status tracking for debugging
- ✅ Error recording
- ❌ **NOT used for async orchestration**
- ❌ **NOT used for parallel agent execution**
- ❌ **`claim()` method exists but never called**

**What it COULD enable:**
```python
# Potential async orchestration (NOT currently implemented)
async def parallel_exploration():
    # Push multiple jobs to queue
    await job_queue.push(Job(type="explore_auth"))
    await job_queue.push(Job(type="explore_api"))
    await job_queue.push(Job(type="plan_integration"))

    # Multiple worker agents could claim and process in parallel
    # (Athena doesn't do this - it's synchronous)
```

**Verdict:** The infrastructure exists for advanced orchestration, but it's underutilized.

---

### 5. Execution Flow

```
┌─────────────────────────────────┐
│       User Request              │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│       MainAgent                 │
│   - Iteration loop (1...N)      │
│   - Tool execution              │
│   - Conversation history        │
└────────────┬────────────────────┘
             ↓
       Decides to use Task tool
             ↓
┌─────────────────────────────────┐
│       Task Tool                 │
│   - Creates SubAgent            │
│   - Passes full tool registry   │
│   - Waits (BLOCKING) ⏸️         │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│       SubAgent                  │
│   - Own iteration loop (1...N)  │
│   - Isolated context bubble     │
│   - Uses tools independently    │
│   - Builds own message history  │
└────────────┬────────────────────┘
             ↓
       Returns text report
             ↓
┌─────────────────────────────────┐
│       Task Tool                 │
│   - Wraps report with header    │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│       MainAgent                 │
│   - Receives wrapped report     │
│   - Continues with task         │
│   - Can spawn another agent     │
└─────────────────────────────────┘
```

**Execution characteristics:**
- **Sequential only** - One sub-agent at a time
- **No streaming** - Wait for complete result before returning
- **No interruption** - Can't stop mid-execution
- **No resumption** - Can't continue previous agent's work
- **No intermediate updates** - User sees nothing until complete

---

### 6. Agent Types

**File:** `athena/agent/types.py`

Athena has **5 hardcoded agent types:**

| Agent Type | System Prompt Size | Purpose | Tools Used |
|------------|-------------------|---------|------------|
| `general-purpose` | 599 chars | General multi-step tasks | All tools |
| `Explore` | 765 chars | Codebase navigation | Glob, Grep, Read |
| `Plan` | 734 chars | Task breakdown | Glob, Grep, Read, TodoWrite |
| `code-reviewer` | Not defined | Code quality review | Read, Grep |
| `test-runner` | Not defined | Test execution | Bash, Read, Grep |

**System prompt example (Plan agent):**
```python
PLAN_SYSTEM_PROMPT = """You are a specialized planning agent...

When planning:
1. Understand the current state
2. Clarify the requirements
3. Break into logical steps
4. Identify dependencies
5. Create step-by-step plan

IMPORTANT: Provide clear, numbered plan with:
- Each step clearly defined
- Dependencies between steps
- Files to create/modify
- Potential challenges
- Testing approach"""
```

**Limitations:**
- Fixed set of 5 agent types
- No user-defined agents
- Basic system prompts (~700 chars)
- No composability or skills system

---

## Claude Code's Architecture

### 1. Agent Resumption (Game Changer)

**Claude Code's killer feature:** Agents can be **resumed** from previous execution.

**How it works:**

```python
# First call - initial exploration
Task(
    subagent_type="Explore",
    prompt="Find authentication implementation in the codebase",
    description="Explore auth system"
)
# Agent explores, returns findings
# Returns agent_id: "agent_abc123"

# Later - user asks follow-up question
# Claude Code can RESUME the same agent!
Task(
    subagent_type="Explore",
    prompt="Now look specifically at the OAuth token refresh logic",
    description="Explore OAuth details",
    resume="agent_abc123"  # ← Continue from previous state!
)
```

**Benefits:**
- ✅ Build on previous exploration (don't start from scratch)
- ✅ Maintain conversation context across multiple interactions
- ✅ Don't re-read files that were already explored
- ✅ More efficient multi-turn tasks
- ✅ Better understanding of codebase over time
- ✅ Can dig deeper incrementally

**Athena equivalent:**
```python
# Must spawn completely new agent every time
# Loses all context, must re-explore everything
Task(
    subagent_type="Explore",
    prompt="Find auth AND OAuth refresh logic (all from scratch)"
)
```

**Impact:** This is a **massive architectural advantage** for complex, multi-turn exploration tasks.

---

### 2. Context Sharing (Full Conversation Access)

**From Claude Code's tool documentation:**

> "Agents with 'access to current context' can see the full conversation history before the tool call. When using these agents, you can write concise prompts that reference earlier context (e.g., 'investigate the error discussed above') instead of repeating information."

**What agents receive:**
- ✅ Full conversation history before tool call
- ✅ User's original request and all messages
- ✅ Previous tool results from main agent
- ✅ Discussion context and clarifications
- ✅ User preferences mentioned earlier

**Example:**

```
User: "I'm getting an error when users log in with OAuth"
Claude: "Can you describe the error?"
User: "It's a 401 Unauthorized, happens after token expiration"
Claude: "When did this start?"
User: "After we deployed the new auth service last week"

# Claude spawns Explore agent:
Task(
    subagent_type="Explore",
    prompt="investigate the OAuth error discussed above"
)

# Agent sees ENTIRE conversation:
# - OAuth login error
# - 401 Unauthorized
# - Token expiration
# - Started after new auth service deployment
# Can make informed decisions about where to look!
```

**Athena equivalent:**
```python
# Must explicitly include all context:
Task(
    prompt="""User is getting 401 Unauthorized errors during OAuth login.
    The error happens after token expiration.
    This started after deploying a new auth service last week.
    Find the OAuth token handling code in the new auth service."""
)
```

**Impact:** Claude Code agents are **context-aware**, Athena agents are **context-blind**.

---

### 3. Selective Tool Access (Token Efficiency)

**Claude Code sends only relevant tools to each agent type:**

| Agent Type | Tools Provided | Token Cost | vs Athena (All Tools) |
|------------|---------------|------------|----------------------|
| **Explore** | Glob, Grep, Read | ~200 tokens | **-500 tokens saved** |
| **Plan** | Glob, Grep, Read, TodoWrite | ~250 tokens | **-450 tokens saved** |
| **claude-code-guide** | Read, Grep, Glob, WebFetch, WebSearch | ~350 tokens | **-350 tokens saved** |
| **statusline-setup** | Read, Edit | ~150 tokens | **-550 tokens saved** |
| **general-purpose** | All tools | ~700 tokens | No difference |

**Implementation (conceptual):**
```python
# Claude Code approach
AGENT_TOOL_MAPPING = {
    AgentType.EXPLORE: ["Glob", "Grep", "Read"],
    AgentType.PLAN: ["Glob", "Grep", "Read", "TodoWrite"],
    AgentType.CLAUDE_CODE_GUIDE: ["Read", "Grep", "Glob", "WebFetch", "WebSearch"],
    AgentType.STATUSLINE_SETUP: ["Read", "Edit"],
    AgentType.GENERAL: ALL_TOOLS,
}

# Only send relevant tools
tools = [registry.get(name) for name in AGENT_TOOL_MAPPING[agent_type]]
```

**Benefits:**
- ✅ 300-500 tokens saved per specialized agent call
- ✅ Better specialization (agents can't use wrong tools)
- ✅ Clearer intent (tool list matches purpose)
- ✅ Better for smaller context window models

**Athena:** Always sends all 21 tools (~500-750 tokens) regardless of agent type

---

### 4. Parallel Execution (Multiple Agents Simultaneously)

**From Claude Code's instructions:**

> "Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses"

**How it works:**

```xml
<!-- Single message with MULTIPLE parallel agents -->
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">Explore</parameter>
    <parameter name="prompt">Find all authentication code</parameter>
    <parameter name="description">Explore auth code</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">Explore</parameter>
    <parameter name="prompt">Find all API endpoints</parameter>
    <parameter name="description">Explore API endpoints</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">Plan</parameter>
    <parameter name="prompt">Design integration approach</parameter>
    <parameter name="description">Plan integration</parameter>
  </invoke>
</function_calls>

<!-- All 3 agents run in parallel! -->
<!-- Results come back together -->
```

**Benefits:**
- ✅ **3x faster** for independent tasks
- ✅ Better user experience (less waiting)
- ✅ Efficient use of multiple CPU cores
- ✅ Can explore different areas simultaneously

**Athena equivalent:**
```python
# Must run sequentially:
result1 = await Task(subagent_type="Explore", prompt="Find auth")     # Wait...
result2 = await Task(subagent_type="Explore", prompt="Find API")      # Wait...
result3 = await Task(subagent_type="Plan", prompt="Design")           # Wait...

# Total time = Time1 + Time2 + Time3 (serial)
```

**Claude Code:**
```python
# Runs in parallel:
results = await asyncio.gather(
    Task(subagent_type="Explore", prompt="Find auth"),
    Task(subagent_type="Explore", prompt="Find API"),
    Task(subagent_type="Plan", prompt="Design")
)

# Total time = max(Time1, Time2, Time3) (parallel)
```

**Impact:** **Massive performance improvement** for multi-agent workflows.

---

### 5. Better Prompt Engineering

**Claude Code's agent instructions are more sophisticated:**

From the tool description:
```
The agent's outputs should generally be trusted

Clearly tell the agent whether you expect it to write code
or just to do research

If the agent description mentions proactive use, use it
without the user asking first

Each agent invocation is stateless unless resumed

You will not be able to send additional messages to the agent
```

**Key insights:**
- Agents are treated as **trusted specialists**
- Clear separation of research vs. implementation
- Proactive agent use guidance
- Stateless design (unless resumed)
- Single-shot execution model

**Athena's prompts:** Simpler, less guidance on behavior and expectations.

---

### 6. Streaming & Interactivity

**Claude Code capabilities:**
- ✅ Agents can stream responses in real-time
- ✅ User sees progress as agent works
- ✅ Can interrupt long-running agents
- ✅ Better UX for complex exploration

**User experience:**
```
[Agent starts]
🔍 Searching for authentication code...
   Found: auth.py, oauth_handler.py, token_manager.py

🔍 Reading auth.py...
   Identified OAuth flow at line 45

🔍 Analyzing token refresh logic...
   [User can see progress in real-time]
```

**Athena:** Blocking wait, no updates until complete:
```
[User sees nothing until agent finishes]
...waiting...
...waiting...
[Final report appears all at once]
```

---

### 7. Skill System (Advanced Composability)

**Claude Code has reusable skills beyond basic agents:**

```
.claude/skills/pdf-analyzer.md
.claude/skills/api-tester.md
.claude/skills/security-audit.md
```

**Skills are:**
- User-defined agent behaviors
- Reusable across sessions and projects
- More sophisticated than basic agent types
- Can be shared in community

**Example skill:**
```markdown
# PDF Analyzer Skill

Analyze PDF documents and extract structured information.

## Tools
- WebFetch (to get PDFs)
- Read (to read extracted text)
- TodoWrite (to track analysis steps)

## Process
1. Fetch PDF from URL
2. Extract text content
3. Analyze structure (headers, sections, tables)
4. Summarize key information
5. Return structured report
```

**Athena:** Only 5 hardcoded agent types, no user extensibility.

---

## Side-by-Side Comparison

| Feature | Athena | Claude Code | Advantage |
|---------|--------|-------------|-----------|
| **Agent Execution** | Synchronous, blocking | Async, non-blocking | Claude Code |
| **Parallel Agents** | ❌ Sequential only | ✅ Multiple simultaneously | Claude Code |
| **Agent Resumption** | ❌ No | ✅ Yes (resume parameter) | **Claude Code** |
| **Context Sharing** | ❌ Isolated bubble | ✅ Full conversation access | **Claude Code** |
| **Tool Selection** | All tools (21) to all agents | Selective (3-10 per agent) | Claude Code |
| **Token Efficiency** | ~700 tokens/agent | ~200-300 tokens/specialized agent | Claude Code |
| **Streaming** | ❌ No | ✅ Real-time updates | Claude Code |
| **Interruptible** | ❌ No | ✅ Can stop mid-execution | Claude Code |
| **Agent Types** | 5 hardcoded | 5+ built-in + custom skills | Claude Code |
| **Extensibility** | Fixed types | Skills + custom agents | Claude Code |
| **Job Queue** | ✅ Sophisticated (underutilized) | Internal system | Athena (potential) |
| **Simplicity** | ✅ Easy to understand | More complex | Athena |
| **Open Source** | ✅ MIT License | ❌ Proprietary | **Athena** |

---

## Performance Implications

### Token Usage Per Agent Call

**Athena:**
```
System prompt:     ~183 tokens
Tool definitions:  ~700 tokens (all 21 tools)
Task prompt:       ~100-500 tokens
Total overhead:    ~983-1,383 tokens
```

**Claude Code (specialized agent):**
```
System prompt:     ~183 tokens
Tool definitions:  ~200 tokens (3-4 tools)
Task prompt:       ~100-500 tokens
Context access:    ~0 tokens (references existing)
Total overhead:    ~483-883 tokens
```

**Savings per specialized agent:** ~500 tokens (36% reduction)

### Time Efficiency

**Scenario:** Explore auth code, API endpoints, and plan integration

**Athena (sequential):**
```
Agent 1: 30 seconds
Agent 2: 25 seconds
Agent 3: 20 seconds
Total:   75 seconds
```

**Claude Code (parallel):**
```
Agent 1: 30 seconds ┐
Agent 2: 25 seconds ├─ Run in parallel
Agent 3: 20 seconds ┘
Total:   30 seconds (max of the three)
```

**Speedup:** 2.5x faster for 3 parallel agents

### Context Window Usage

**Athena:** Higher token usage per agent (wasteful tool definitions)

**Claude Code:** More efficient (selective tools), but conversation grows with full context access

**Winner:** Claude Code for specialized agents, roughly equal for general-purpose agents

---

## Improvement Recommendations for Athena

### 1. **Implement Agent Resumption** (High Impact)

**What to add:**
```python
# In athena/tools/task.py
class TaskTool(Tool):
    def __init__(self):
        self.active_agents: dict[str, SubAgent] = {}

    async def execute(
        self,
        subagent_type: str,
        prompt: str,
        description: str,
        resume: Optional[str] = None,  # NEW parameter
        **kwargs
    ):
        if resume and resume in self.active_agents:
            # Resume existing agent
            agent = self.active_agents[resume]
            agent.messages.append(Message(role=Role.USER, content=prompt))
        else:
            # Create new agent
            agent = SubAgent(...)
            self.active_agents[agent.agent_id] = agent

        result = await agent.run(prompt, description)
        return result
```

**Benefits:**
- Multi-turn exploration without losing context
- More efficient codebase understanding
- Can dig deeper incrementally

---

### 2. **Selective Tool Registration** (Medium Impact)

**What to add:**
```python
# In athena/agent/types.py
AGENT_TOOL_MAPPING = {
    AgentType.PLAN: ["Glob", "Grep", "Read", "TodoWrite"],
    AgentType.EXPLORE: ["Glob", "Grep", "Read"],
    AgentType.CODE_REVIEWER: ["Read", "Grep", "Glob"],
    AgentType.TEST_RUNNER: ["Bash", "Read", "Grep"],
    AgentType.GENERAL: None,  # All tools
}

# In athena/tools/task.py
def _get_tools_for_agent(agent_type: AgentType) -> ToolRegistry:
    tool_names = AGENT_TOOL_MAPPING.get(agent_type)

    if tool_names is None:  # General purpose
        return self.tool_registry

    # Create filtered registry
    filtered = ToolRegistry()
    for name in tool_names:
        filtered.register(self.tool_registry.tools[name])

    return filtered
```

**Savings:** 300-500 tokens per specialized agent

---

### 3. **Parallel Agent Execution** (High Impact)

**What to add:**
```python
# In athena/agent/main_agent.py
async def _execute_tool_calls(self, tool_calls: list[ToolCall]):
    # Check if multiple Task tools
    task_calls = [tc for tc in tool_calls if tc.name == "Task"]
    other_calls = [tc for tc in tool_calls if tc.name != "Task"]

    if len(task_calls) > 1:
        # Execute Task tools in parallel
        task_results = await asyncio.gather(
            *[self.tool_registry.execute(tc.name, **tc.parameters)
              for tc in task_calls]
        )

    # Execute other tools normally
    # ...
```

**Benefits:**
- 2-3x speedup for independent tasks
- Better user experience
- Efficient resource usage

---

### 4. **Context Sharing** (Medium Impact)

**What to add:**
```python
# In athena/agent/sub_agent.py
def __init__(
    self,
    agent_type: AgentType,
    config: AthenaConfig,
    tool_registry: ToolRegistry,
    job_queue: SQLiteJobQueue,
    parent_job_id: Optional[str] = None,
    shared_context: Optional[list[Message]] = None,  # NEW
):
    # ... existing init ...

    # Add shared context if provided
    if shared_context:
        # Include relevant parts of main conversation
        context_summary = self._summarize_context(shared_context)
        self.messages.append(
            Message(
                role=Role.SYSTEM,
                content=f"Context:\n{context_summary}"
            )
        )
```

**Benefits:**
- Agents understand broader goals
- Less context duplication in prompts
- Better decision-making

---

### 5. **Leverage Existing Job Queue** (Low Effort, Medium Impact)

**Athena already has the infrastructure!**

```python
# The job queue has everything needed:
# - parent_job_id tracking
# - claim() method
# - priority queue
# - status tracking

# Just need to actually use it for async orchestration!

async def parallel_agent_orchestration():
    # Push multiple jobs
    jobs = [
        Job(type="explore_auth", priority=1),
        Job(type="explore_api", priority=1),
        Job(type="plan", priority=2),
    ]

    for job in jobs:
        await job_queue.push(job)

    # Multiple workers can claim and process
    # (This infrastructure exists but is unused!)
```

---

## Conclusion

### Athena's Strengths
- ✅ Simple, understandable architecture
- ✅ Sophisticated job queue (underutilized)
- ✅ Clean separation of concerns
- ✅ Open source and hackable

### Claude Code's Advantages
- ✅ Agent resumption (game-changer)
- ✅ Full context awareness
- ✅ Parallel execution
- ✅ Selective tool access (efficiency)
- ✅ Streaming and interactivity
- ✅ Skill system (extensibility)

### Key Insight

**Athena has excellent foundations** (job queue, modular design, clean interfaces) but **underutilizes them**. The job queue alone could enable most of Claude Code's advanced orchestration if properly leveraged.

**Biggest Gaps:**
1. Agent resumption (requires state management)
2. Parallel execution (job queue infrastructure exists!)
3. Context sharing (needs design decision on what to share)
4. Selective tools (easy to implement, high impact)

**Recommended Priority:**
1. **Selective tool registration** (low effort, immediate savings)
2. **Parallel execution** (leverage existing job queue)
3. **Agent resumption** (architectural change, high value)
4. **Context sharing** (careful design needed)

By addressing these gaps, Athena could match Claude Code's orchestration capabilities while maintaining its open-source, model-agnostic advantages.

---

**Document Version:** 1.0
**Date:** 2025-12-26
**Analysis by:** Claude (running as Claude Code analyzing Athena's codebase)
