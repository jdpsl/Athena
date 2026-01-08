# Athena Development Roadmap

## Executive Summary

This document outlines how Athena compares to Claude Code and provides a strategic roadmap for improvements to maintain competitiveness while preserving unique advantages.

---

## Athena vs Claude Code: Current State

### Architectural Comparison

| Aspect | **Athena** | **Claude Code** |
|--------|------------|-----------------|
| **Open Source** | ✅ MIT License | ❌ Proprietary |
| **Model Support** | ✅ Any OpenAI-compatible API (LM Studio, Groq, Ollama, etc.) | ❌ Claude models only (Anthropic) |
| **Cost** | ✅ Free (local models) or variable (API cost) | 💰 Anthropic API pricing |
| **Codebase Size** | ~36 Python files, smaller/simpler | Larger, more mature |
| **Architecture** | SQLite job queue, sub-agents | Advanced agent orchestration |

### Core Capabilities

#### Tools Available

**Athena (21 tools)**:
- File ops: Read, Write, Edit, Delete, Move, Copy, ListDir, MakeDir (8)
- Search: Glob, Grep (2)
- Git: Status, Diff, Commit, Log, Branch (5)
- Execution: Bash (1)
- Web: WebSearch, WebFetch (2)
- Agent: Task (spawn sub-agents), TodoWrite (2)
- User: AskUserQuestion (1)

**Claude Code (~18+ tools)**:
- Similar file operations (Read, Write, Edit, Glob, Grep)
- Git operations with more sophisticated handling
- Bash with better safety/sandboxing
- Task (spawn agents) with more agent types
- TodoWrite, WebFetch, WebSearch
- Additional: Skill system, SlashCommand system, NotebookEdit
- MCP server integration (can extend with unlimited external tools)

#### Agent Types

**Athena** (9 agents):
- Explore
- Plan
- code-reviewer
- test-runner
- research
- scientist
- security-researcher
- athena-docs (documentation lookup)
- general-purpose

**Claude Code** (5-6+ agents):
- Explore
- Plan
- general-purpose
- statusline-setup
- claude-code-guide (documentation lookup)
- Custom skills (extensible)

---

## Key Differentiators

### Where Athena Wins

1. **🔓 Fully Open Source**
   - Can inspect/modify all code
   - No vendor lock-in
   - Self-hostable

2. **🔌 Model Flexibility**
   - Works with **any** OpenAI-compatible API
   - LM Studio, Ollama, Groq, ChatGPT, etc.
   - Fallback mode for models without function calling

3. **💰 Cost Control**
   - Free with local models (Llama 3, Mistral, Qwen)
   - Pay only for API if using cloud providers
   - No per-token Anthropic costs

4. **🛠️ Fallback Mode**
   - Text-based tool calling: `TOOL[Name]{params}`
   - Works with models that lack function calling
   - Massive compatibility advantage

5. **🧪 Experimental Freedom**
   - Can hack on the codebase
   - Add custom tools easily
   - No restrictions

6. **🤖 More Specialized Agents**
   - 9 built-in agent types vs Claude Code's 5-6
   - Unique agents: research (library investigation), scientist (data analysis), security-researcher (CVE scanning)
   - Task-specific expertise for common development workflows

### Where Claude Code Wins

1. **🧠 Model Quality**
   - Uses Claude Sonnet 4.5 (extremely capable)
   - Better reasoning, coding, and planning
   - More reliable tool usage

2. **🔒 Sandboxing & Safety**
   - Better isolation for code execution
   - More security guardrails
   - Professional-grade reliability

3. **📚 Documentation Agent**
   - `claude-code-guide` agent can look up official docs
   - Better self-help capabilities
   - Stays updated with latest features

4. **🎯 Polish & UX**
   - More mature system prompt engineering
   - Better error handling
   - Refined multi-agent coordination

5. **🔌 MCP Integration**
   - Model Context Protocol support
   - Can connect to external servers (databases, APIs, etc.)
   - Extensible beyond built-in tools

6. **📓 Notebook Support**
   - NotebookEdit tool for Jupyter notebooks
   - Better data science workflow

7. **⚙️ Skill System**
   - Reusable, composable agent behaviors
   - More sophisticated than basic sub-agents

---

## Strategic Improvements (Priority Order)

### 1. 🔌 MCP (Model Context Protocol) Support ⭐️ HIGHEST IMPACT ✅ **COMPLETED**

**Status:** Fully implemented and pushed to GitHub (2025-12-27)

**What was added:**
- `athena/mcp/client.py` - Base MCPClient abstract class
- `athena/mcp/stdio_client.py` - Stdio transport (subprocess)
- `athena/mcp/http_client.py` - HTTP transport
- `athena/mcp/manager.py` - MCPClientManager for orchestrating connections
- `athena/mcp/tool_wrapper.py` - Wraps MCP tools as Athena tools
- `athena/mcp/schema_converter.py` - JSON Schema to ToolParameter conversion
- Slash commands: `/mcp-list`, `/mcp-add`, `/mcp-remove`, `/mcp-enable`, `/mcp-disable`
- Persistent configuration in `~/.athena/config.json`
- Dynamic tool discovery and registration

**Example use cases now supported:**
- Database queries (Postgres, MySQL via MCP servers)
- Cloud APIs (AWS, GCP, Azure via MCP servers)
- Code analysis tools (SonarQube, ESLint via MCP servers)
- Documentation servers (ReadTheDocs, DevDocs via MCP servers)
- Filesystem operations (via mcp-server-filesystem)

**Impact achieved:** Massive - Athena can now connect to unlimited external tools via MCP ecosystem

---

### 2. 📚 Self-Documentation Agent ✅ **COMPLETED**

**Status:** Fully implemented (2025-12-27)

**What was added:**
- Added `AgentType.ATHENA_DOCS` to `athena/agent/types.py`
- Created comprehensive system prompt for documentation assistance
- Added `_is_documentation_question()` method to detect doc questions
- Added `_spawn_docs_agent()` method to spawn specialized docs agent
- Integrated into interactive loop to automatically trigger on questions
- Agent has access to Glob, Grep, and Read tools for documentation lookup

**Triggers (automatically detected):**
- "How do I configure web search?"
- "What tools does Athena have?"
- "Can Athena do X?"
- "How do I use MCP?"
- "What commands are available?"
- And many more documentation-related patterns

**Impact achieved:** High - Users can now ask Athena about itself and get accurate answers by searching actual documentation

---

### 3. 🎯 Context Compression & Management

**Current problem:** No mechanism to compress old messages

**What to add:**
```python
# athena/context/compressor.py
class ContextCompressor:
    """Compress old messages to preserve context window."""

    async def compress_history(
        self,
        messages: list[Message],
        max_tokens: int
    ) -> list[Message]:
        """Summarize old messages when approaching limit."""
        # Keep: System, last N messages
        # Compress: Middle messages into summary
        # Result: More room for current work
```

**Strategies:**
- Summarize tool results after N turns
- Keep only recent file reads
- Compress old bash outputs
- Rolling window of conversation

**Effort:** Medium | **Impact:** High (better for long sessions)

---

### 4. 📓 Jupyter Notebook Support

**Current gap:** No notebook editing capability

**What to add:**
```python
# athena/tools/notebook.py
class NotebookEditTool(Tool):
    """Edit Jupyter notebook cells."""

    async def execute(
        self,
        notebook_path: str,
        cell_id: str,
        new_source: str,
        edit_mode: str = "replace"  # replace, insert, delete
    ) -> ToolResult:
        # Read .ipynb (JSON)
        # Modify cell
        # Write back
```

**Use cases:**
- Data science workflows
- Interactive tutorials
- Exploratory coding

**Effort:** Low | **Impact:** Medium (expands user base)

---

### 5. 🔒 Enhanced System Prompt (Claude Code Quality)

**Current:** 850 words, basic guidelines
**Target:** 1,500+ words with professional practices

**Key additions:**
```python
ENHANCED_SYSTEM_PROMPT = """
+ Git Safety Protocol:
  - Never force push to main
  - Always check authorship before amend
  - Use heredoc for commit messages
  - Retry git push with exponential backoff

+ Code Quality Standards:
  - Avoid over-engineering
  - No unnecessary abstractions
  - Security awareness (OWASP top 10)
  - Test before committing

+ Error Handling:
  - Graceful degradation
  - Informative error messages
  - Retry logic for network ops

+ Professional Workflow:
  - Read before edit (enforced)
  - Commit message conventions
  - PR creation guidelines
  - Branch naming standards
"""
```

**Effort:** Low | **Impact:** High (better output quality)

---

### 6. ⚡ Streaming Responses

**Current:** Waits for complete response
**Target:** Show output as generated

**What to add:**
```python
# athena/llm/client.py
async def stream_completion(self, messages: list[Message]):
    """Stream response chunks as they arrive."""
    async for chunk in self.client.chat.completions.create(
        model=self.config.model,
        messages=messages,
        stream=True
    ):
        yield chunk.choices[0].delta.content
```

**Benefits:**
- Feels more responsive
- User sees thinking in real-time
- Can interrupt long responses

**Effort:** Medium | **Impact:** Medium (UX improvement)

---

### 7. 🧪 Skill System

**Current:** Only basic sub-agents
**Target:** Reusable, composable behaviors

**What to add:**
```python
# athena/skills/base.py
class Skill:
    """Reusable agent behavior."""

    name: str
    prompt: str  # Loaded from .athena/skills/{name}.md
    tools: list[str]

# Usage:
# .athena/skills/pdf-analyzer.md
# .athena/skills/api-tester.md
# .athena/skills/security-audit.md
```

**Use cases:**
- PDF analysis
- API testing
- Security audits
- Custom workflows

**Effort:** Medium | **Impact:** High (extensibility)

---

### 8. 🛡️ Better Git Workflow

**Current:** Basic git operations
**Target:** Claude Code-level sophistication

**Improvements:**
- PR creation with `gh` CLI
- Retry logic for network failures
- Pre-commit hook handling
- Branch naming validation
- Commit message templates

**Example:**
```python
# athena/tools/git.py - Enhanced GitCommitTool
async def execute(self, message: str, **kwargs):
    # Check authorship first
    # Use heredoc for message
    # Handle pre-commit hooks
    # Auto-amend if hook modifies files
    # Retry push with exponential backoff
```

**Effort:** Medium | **Impact:** Medium (professional workflow)

---

### 9. 📊 Better Tool Selection (Selective Registration)

**Current problem:** All 21 tools sent every time = ~500-750 tokens
**Target:** Only send relevant tools per agent

**Implementation:**
```python
# athena/agent/types.py
AGENT_TOOL_MAPPING = {
    AgentType.PLAN: ["Glob", "Grep", "Read", "TodoWrite"],
    AgentType.EXPLORE: ["Glob", "Grep", "Read"],
    AgentType.CODE_REVIEWER: ["Read", "Grep", "Glob"],
    AgentType.GENERAL: ALL_TOOLS,
}
```

**Savings:** 300-500 tokens per sub-agent call

**Effort:** Low | **Impact:** Medium (efficiency)

---

### 10. 🔍 Better Error Recovery ✅ **COMPLETED**

**Status:** Fully implemented (2025-12-28)

**What was added:**
- `athena/errors/classifier.py` - Intelligent error classification system
- `athena/errors/strategies.py` - Retry strategies (exponential/linear backoff, rate limiting)
- `athena/errors/recovery.py` - Main ErrorRecovery orchestration class
- Integrated into LLM client for automatic API retry
- Integrated into ToolRegistry with smart retry logic
- Comprehensive test suite demonstrating all features

**Features implemented:**
- **Error Classification:** Automatically categorizes errors (network, timeout, rate limit, file not found, permission, syntax, validation)
- **Intelligent Retry:** Exponential backoff for network/timeout, aggressive backoff for rate limits, no retry for file/permission errors
- **LLM API Protection:** API calls automatically retry on network failures with exponential backoff
- **Tool Safety:** Read-only tools (Glob, Grep, Read) retry on failure; write tools (Write, Edit, Delete) never retry to prevent data corruption
- **Helpful Hints:** Provides recovery suggestions for each error type
- **Configurable:** Can enable/disable recovery per component

**Impact achieved:** High - System is much more resilient to transient failures

---

## Implementation Timeline

### Phase 1: Quick Wins (1-2 weeks)

Priority improvements with low effort and high impact:

1. ✅ **Self-documentation agent** - Low effort, high UX impact
2. ✅ **Enhanced system prompt** - Low effort, better outputs
3. ✅ **Selective tool registration** - Low effort, efficiency gain
4. ✅ **Notebook support** - Low effort, expands use cases

**Expected outcomes:**
- Better user experience
- More professional outputs
- Support for data science workflows
- Token efficiency improvements

---

### Phase 2: Core Infrastructure (2-4 weeks)

Critical improvements for production readiness:

5. ✅ **MCP support** - Medium effort, massive extensibility
6. ✅ **Context compression** - Medium effort, critical for long sessions
7. ✅ **Better git workflow** - Medium effort, professional polish

**Expected outcomes:**
- Extensibility matching Claude Code
- Better handling of long conversations
- Professional development workflows

---

### Phase 3: Polish & Advanced (4-8 weeks)

Advanced features for power users:

8. ✅ **Streaming responses** - Medium effort, UX improvement
9. ✅ **Skill system** - Medium effort, power users
10. ✅ **Error recovery** - Medium effort, reliability

**Expected outcomes:**
- Modern UX expectations met
- Advanced customization capabilities
- Production-grade reliability

---

## Biggest Competitive Advantages to Maintain

**Don't lose these core differentiators:**

1. ✅ **Open source** - Core value proposition
2. ✅ **Model flexibility** - Works with any OpenAI-compatible API
3. ✅ **Fallback mode** - Unique feature Claude Code doesn't have
4. ✅ **Local execution** - Privacy & cost benefits
5. ✅ **Simplicity** - Smaller, hackable codebase

---

## Recommended Starting Point

If prioritizing Athena's roadmap for maximum impact:

### Must-Have (Next 2 weeks)

1. **MCP support** - Game-changer for extensibility
2. **Enhanced system prompt** - Immediate quality improvement
3. **Self-documentation agent** - Better user experience

**Rationale:** These three provide the biggest competitive leap with manageable effort.

### Should-Have (Next month)

4. **Context compression** - Critical for production use
5. **Selective tool registration** - Efficiency for smaller models
6. **Streaming responses** - Modern UX expectation

**Rationale:** These address core infrastructure needs and user expectations.

### Nice-to-Have (Next quarter)

7. **Skill system** - Power user features
8. **Better git workflow** - Professional polish
9. **Notebook support** - Expand user base
10. **Error recovery** - Production reliability

**Rationale:** These are polish and advanced features that can be added iteratively.

---

## Success Metrics

Track these to measure improvement:

### User Experience
- Time to first response (streaming)
- Number of context window errors (compression)
- User retention rate
- Feature usage statistics

### Technical Performance
- Tokens per request (selective tools)
- Average conversation length before /clear
- Tool call success rate
- Error recovery success rate

### Ecosystem Growth
- Number of MCP servers integrated
- Custom skills created by users
- Contributors to codebase
- GitHub stars/forks

---

## Conclusion

Athena has a strong foundation with unique advantages (open source, model flexibility, fallback mode). By implementing these strategic improvements in phases, Athena can:

1. **Match Claude Code's capabilities** in core areas (MCP, context management)
2. **Exceed Claude Code** in flexibility and cost-effectiveness
3. **Maintain unique advantages** that Claude Code cannot replicate

The key is to focus on high-impact improvements first (MCP, enhanced prompts, self-docs) while preserving the simplicity and openness that make Athena valuable.

---

---

## Research Topics & Future Exploration

These are experimental ideas under consideration. Not scheduled for implementation, but worth exploring further.

### AI-Driven Context Compression (CompressContext Tool)

**Concept:** Give the AI a `CompressContext` tool and let it decide when to compress conversation history, rather than using automatic thresholds.

**How it would work:**
```python
class CompressContextTool(Tool):
    """Let AI compress conversation when appropriate."""

    async def execute(self, keep_recent: int = 5, preserve_tool_types: list[str] = None):
        """
        Args:
            keep_recent: Number of recent exchanges to keep full (default: 5)
            preserve_tool_types: Tool results to preserve (e.g., ["Read", "Glob"])
        """
        # Compress everything except recent messages and specified tools
```

**Potential benefits:**
- ✅ Model knows when it's "done" with information
- ✅ Can compress after completing a sub-task (e.g., after exploring 20 files)
- ✅ Smarter than heuristics - AI decides what to preserve
- ✅ Could improve inference speed (fewer tokens = faster responses)
- ✅ Optional/explicit - doesn't change current behavior

**Challenges:**
- ⚠️ Tool call dependency chains (Glob → Read → Edit needs the file list)
- ⚠️ Model might forget to compress or over-compress
- ⚠️ Need strong system prompt guidance on when to use
- ⚠️ Extra tool call overhead
- ⚠️ Quality degradation if compression is too aggressive

**Use cases:**
- Long exploratory sessions (read 50 files, compress after decision made)
- After installing dependencies (compress bash output)
- After completing a distinct sub-task
- Before switching contexts/topics

**Status:** Under consideration. Performance benefits need validation. Tool call dependencies are a key concern.

**Date added:** 2026-01-07

---

**Document Version:** 1.2
**Last Updated:** 2026-01-07
**Changes:** Added 3 new specialized agents (research, scientist, security-researcher)
**Author:** Claude Code Analysis
