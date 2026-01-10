# Memory & User Personalization System

## Overview

Athena will remember information about the user across sessions to provide personalized, context-aware assistance. This includes coding preferences, personal context, and learned patterns.

## Core Concept

**Problem**: Athena starts fresh every session. Users have to repeat preferences, explain context, and re-establish patterns.

**Solution**: Build a memory system that learns and remembers:
- Who the user is (name, background, interests)
- How they like to code (style, tools, frameworks)
- Personal context (family, projects, goals)
- Patterns and preferences discovered over time

## Key Insight: Different Agents Need Different Memory

**Critical Discovery**: Not all agents need all memories!

### Coding/Execution Agent
- **Purpose**: Write code, fix bugs, implement features
- **Needs**: Coding preferences, tool choices, formatting rules
- **Doesn't need**: Personal context (rarely relevant when writing code)

**Example:**
```
User: "Fix this bug in auth.py"
Coding Agent: [Uses TypeScript preference, pytest testing, functional style]
Coding Agent: [Doesn't need to know about user's kids or interests]
```

### Planning Agent
- **Purpose**: Design solutions, suggest approaches, make recommendations
- **Needs**: Coding preferences + personal context + project goals
- **Uses personal context**: To make relevant, tailored suggestions

**Example:**
```
User: "I want to build a game"

Planning Agent (without personal memory):
"Let's build a web-based platformer with Three.js..."

Planning Agent (with personal memory - knows user has kids):
"Since you have kids Emma (7) and Lucas (5), how about an educational
math game that teaches addition? We could use TypeScript (your preference),
add pytest tests, and make it kid-friendly with colorful animations."
```

### Research/Exploration Agent
- **Purpose**: Search codebase, gather information, explore files
- **Needs**: May need any context depending on research goal
- **Flexible**: Different queries need different context

**This means**: Memory injection should be **agent-aware**!

## Memory Storage

### Location
`~/.athena/user_profile.json`

**Why global?**
- Memories follow the user across all projects
- Coding preferences are usually consistent
- Personal context doesn't change per-project

### Structure (Agent-Aware Design)

```json
{
  "version": "1.0",
  "user": {
    "name": "John",
    "timezone": "PST",
    "created_at": "2026-01-09T10:30:00Z",
    "last_updated": "2026-01-09T15:45:00Z"
  },
  "memories": [
    {
      "id": "mem_001",
      "type": "personal",
      "category": "family",
      "content": "Has two kids: Emma (7) and Lucas (5)",
      "source": "explicit",
      "created_at": "2026-01-09T10:30:00Z",
      "confidence": 1.0,
      "tags": ["personal", "family"],
      "inject_for": ["planning", "research"]
    },
    {
      "id": "mem_002",
      "type": "coding_preference",
      "category": "language",
      "content": "Prefers TypeScript over JavaScript",
      "source": "implicit",
      "created_at": "2026-01-09T11:15:00Z",
      "confidence": 0.9,
      "usage_count": 5,
      "tags": ["coding", "language", "typescript"],
      "inject_for": ["coding", "planning", "research"]
    },
    {
      "id": "mem_003",
      "type": "project_pattern",
      "category": "testing",
      "content": "Always writes unit tests with pytest",
      "source": "implicit",
      "created_at": "2026-01-09T12:00:00Z",
      "confidence": 0.85,
      "usage_count": 3,
      "tags": ["coding", "testing", "pytest"],
      "inject_for": ["coding", "planning"]
    },
    {
      "id": "mem_004",
      "type": "communication",
      "category": "style",
      "content": "Prefers concise responses without emoji",
      "source": "manual",
      "created_at": "2026-01-09T14:20:00Z",
      "confidence": 1.0,
      "tags": ["communication", "style"],
      "inject_for": ["coding", "planning", "research"]
    },
    {
      "id": "mem_005",
      "type": "personal",
      "category": "interests",
      "content": "Interested in building educational tools",
      "source": "explicit",
      "created_at": "2026-01-09T15:00:00Z",
      "confidence": 1.0,
      "tags": ["personal", "interests", "project"],
      "inject_for": ["planning"]
    }
  ]
}
```

**New field: `inject_for`**
- Array of agent types that should receive this memory
- Options: `["coding", "planning", "research"]` or any combination
- Allows fine-grained control over what each agent sees

## Memory Types

### 1. Personal Information
- **Name, pronouns**: "Call me Alex", "Use they/them pronouns"
- **Background**: "I'm a senior engineer at Google", "I teach high school CS"
- **Family**: "I have two kids", "Names are Emma and Lucas"
- **Interests**: "I love building educational tools", "Interested in game development"
- **Context**: "Working on a startup", "Learning Rust on weekends"

**Examples:**
- "Oh, that would be perfect for Emma and Lucas to learn programming!"
- "As a teacher, you might want to structure this with clear learning objectives"

### 2. Coding Preferences
- **Languages**: "Prefers TypeScript", "Avoids Python 2.x"
- **Style**: "Uses functional programming", "Prefers arrow functions", "4-space indentation"
- **Frameworks**: "Uses React + Vite", "Prefers FastAPI over Flask"
- **Tools**: "Uses pnpm not npm", "Prefers pytest", "VSCode user"
- **Patterns**: "Always uses async/await", "Avoids classes, prefers pure functions"

**Examples:**
- "I'll use TypeScript since that's your preference"
- "Creating pytest tests as usual"

### 3. Project Patterns
- **Testing**: "Always adds unit tests", "Prefers TDD approach"
- **Documentation**: "Likes detailed comments", "Prefers inline docs over separate files"
- **Architecture**: "Uses MVVM pattern", "Prefers microservices"
- **Git**: "Uses conventional commits", "Prefers squash merges"
- **Quality**: "Runs linters before committing", "Type hints on all functions"

**Examples:**
- "I've added pytest tests as you usually prefer"
- "Using conventional commit format: feat: Add user authentication"

### 4. Communication Style
- **Verbosity**: "Prefers concise responses", "Likes detailed explanations"
- **Tone**: "Professional tone", "Casual and friendly"
- **Formatting**: "No emoji", "Use bullet points", "Code-first explanations"
- **Updates**: "Show progress frequently", "Only notify when complete"

**Examples:**
- (Adjusts response length and style accordingly)

### 5. Avoid Patterns (Anti-preferences)
- "Never use classes in Python (only functions)"
- "Don't add comments unless complex logic"
- "Avoid creating new files unless necessary"
- "Don't use var in JavaScript (only const/let)"

**Examples:**
- "Using functions as you prefer (avoiding classes)"

## Memory Creation Methods

### 1. Explicit (User tells Athena directly)

**User**: "Remember that I prefer snake_case for Python variables"
**User**: "My name is Sarah, I'm a data scientist"
**User**: "I have a dog named Max"

**Athena**: "✓ Remembered: You prefer snake_case for Python variables"

**Properties:**
- `source: "explicit"`
- `confidence: 1.0`
- Immediate storage
- User knows it's remembered

### 2. Implicit (Athena observes patterns)

**Scenario**: User asks Athena to write Python code 5 times, always uses pytest
**After 3rd time**: Athena notices pattern
**After 5th time**:

**Athena**: "I've noticed you consistently use pytest for testing. Should I remember this as your preferred testing framework?"

**User**: "Yes" → Memory created
**User**: "No" or ignore → Don't save, don't ask again for a while

**Properties:**
- `source: "implicit"`
- `confidence: 0.7-0.9` (based on frequency)
- `usage_count: 5` (how many times pattern observed)
- Requires user confirmation before saving

### 3. Manual (Slash commands)

```bash
# Add memory
/remember I prefer async/await over callbacks
/remember My timezone is EST
/remember I have two cats: Luna and Oliver

# View memories
/memory list
/memory show personal
/memory show coding

# Search memories
/memory search typescript
/memory search family

# Delete memory
/memory delete mem_042
/memory delete all personal  # Delete all memories in category

# Edit memory
/memory edit mem_042 "I prefer TypeScript for frontend, Python for backend"
```

## How Memories Are Used: Agent-Aware Injection

**Approach**: Inject memories based on which agent is running.

### Implementation

```python
def get_memories_for_agent(agent_type: str, all_memories: list) -> list:
    """Filter memories based on agent type."""
    return [
        memory for memory in all_memories
        if agent_type in memory.get("inject_for", [])
    ]

# When generating system prompt
if agent_type == "coding":
    memories = get_memories_for_agent("coding", all_memories)
    # Result: Only coding preferences, avoid patterns, communication style

elif agent_type == "planning":
    memories = get_memories_for_agent("planning", all_memories)
    # Result: Coding preferences + personal context + project interests

elif agent_type == "research":
    memories = get_memories_for_agent("research", all_memories)
    # Result: All potentially relevant memories
```

### Example: Coding Agent System Prompt

```
USER PROFILE (Coding Agent):
- Prefers: TypeScript, functional programming, pytest
- Style: snake_case, 4 spaces, type hints
- Avoid: Classes in Python (use functions), var keyword
- Communication: Concise, no emoji

[Personal context NOT included - not relevant for implementation]
```

**Token usage**: ~150 tokens (lean and focused)

### Example: Planning Agent System Prompt

```
USER PROFILE (Planning Agent):
CODING:
- Prefers: TypeScript, functional programming, pytest
- Style: snake_case, 4 spaces, type hints
- Tools: pnpm, docker, VSCode

PERSONAL:
- Name: John
- Has kids: Emma (7), Lucas (5)
- Interests: Building educational tools
- Background: Senior engineer, teaches on weekends

COMMUNICATION:
- Style: Concise, no emoji
```

**Token usage**: ~250 tokens (includes personal context for better recommendations)

### Example: Research Agent System Prompt

```
USER PROFILE (Research Agent):
[May include any memories depending on research goal]
- Usually gets all coding preferences
- May get personal context if relevant to search
- Flexible based on query
```

**Token usage**: Variable (contextual)

### Benefits of Agent-Aware Approach

**✓ Token efficient**
- Coding agents stay lean (~150 tokens)
- Planning agents get rich context (~250 tokens)
- No wasted tokens on irrelevant info

**✓ Each agent gets exactly what it needs**
- Coding: Technical preferences only
- Planning: Technical + personal for better suggestions
- Research: Flexible based on task

**✓ Scales well**
- Can have 50+ memories total
- Each agent only sees 10-20 relevant ones
- No retrieval/RAG complexity needed

**✓ Simple to implement**
- Just filter by `inject_for` field
- No semantic search required
- No embeddings needed

**✓ User control**
- User can adjust `inject_for` per memory
- `/memory edit mem_001 --inject planning,research` (add to specific agents)
- Transparent and controllable

## Memory Categories & Tagging

Each memory can have:
- **Type**: `personal`, `coding_preference`, `project_pattern`, `communication`, `avoid_pattern`
- **Category**: `family`, `language`, `testing`, `style`, `framework`, etc.
- **Tags**: `["typescript", "coding", "language"]` for flexible filtering

**Use cases:**
- Show only coding preferences: `/memory show coding`
- Search for family info: `/memory search family`
- Filter by confidence: Show only high-confidence memories in prompt

## Open Questions & Design Decisions

### 1. Should Athena mention when using memories?

**Option A: Silent (Natural)**
```
User: "Build a simple game"
Athena: "How about a math puzzle game for Emma and Lucas?"
```
(User might wonder: How did Athena know about Emma and Lucas?)

**Option B: Transparent (Explicit)**
```
User: "Build a simple game"
Athena: "I remember you have kids Emma (7) and Lucas (5).
How about a math puzzle game for their age group?"
```
(Clear Athena is using memory, but might feel robotic)

**Option C: Subtle (Tagged)**
```
User: "Build a simple game"
Athena: "How about a math puzzle game for Emma and Lucas? 📝"
```
(Small indicator that memory was used, unobtrusive)

**Option D: Debug Mode**
```
Normal: Silent
With /debug on: Shows "[Memory: mem_001, mem_005 used]"
```

### 2. Implicit memory - how aggressive should detection be?

**Conservative:**
- Require 5+ instances of same pattern
- Always ask for confirmation
- High confidence threshold (0.9+)

**Moderate:**
- Detect after 3 instances
- Ask for confirmation
- Medium confidence (0.7+)

**Aggressive:**
- Detect after 2 instances
- Auto-save with low confidence
- Let user delete if wrong

### 3. Memory staleness & updates

**Scenario**: User preferred React 6 months ago, now uses Svelte

**Option A: Overwrite**
- New memory replaces old
- Single source of truth
- Lose history

**Option B: Timestamp Priority**
- Keep all, use most recent
- Historical record maintained
- Can see evolution

**Option C: Confidence Decay**
```json
{
  "content": "Prefers React",
  "created_at": "2025-07-01",
  "confidence": 0.5,  // Decayed from 1.0 over 6 months
  "superseded_by": "mem_156"
}
```

**Option D: Ask for Update**
```
Athena: "I remember you preferred React, but I notice you're using
Svelte now. Should I update this preference?"
```

### 4. Privacy & Control

**View all memories:**
```bash
/memory list
# Shows:
# Personal (5 memories)
# Coding Preferences (12 memories)
# Project Patterns (8 memories)
# Communication (3 memories)
```

**Delete memories:**
```bash
/memory delete mem_042           # Delete specific
/memory delete category personal # Delete category
/memory clear                    # Delete all (with confirmation)
```

**No export/import** (per user request)
- Keeps things simple
- Memories are session-specific, not portable

### 5. Memory conflicts

**Scenario**:
- Memory 1: "Prefers TypeScript"
- Memory 2: "Uses Python for scripting"
- User asks: "Create a script"

**Which language to use?**

**Option A: Most specific wins**
- "script" + "Python for scripting" → Python
- More specific context takes priority

**Option B: Most recent wins**
- Check timestamps, use newer preference

**Option C: Ask user**
- "I see you prefer TypeScript but also use Python for scripts. Which should I use?"

**Option D: Confidence-based**
- Use confidence scores to resolve conflicts

### 6. Multi-user environments

**Scenario**: Shared machine, multiple developers

**Option A: Ignore (out of scope)**
- Single user per ~/.athena/
- User's responsibility to manage

**Option B: User profiles**
```bash
/profile switch alice
/profile switch bob
```
(Probably overkill for v1)

## Implementation Plan (Agent-Aware Approach)

### Phase 1: Basic Manual Memory with Agent-Aware Injection
**Core functionality:**
- `/remember <text>` command (auto-detect type and inject_for)
- `/memory list` to view all memories
- `/memory delete <id>` to remove
- Store in `~/.athena/user_profile.json`
- Implement `inject_for` field with agent-type filtering
- Auto-assign `inject_for` based on memory type:
  - Coding preferences → `["coding", "planning", "research"]`
  - Personal → `["planning", "research"]`
  - Communication → `["coding", "planning", "research"]`

**Goal**: Get agent-aware memory working from day 1

**Example:**
```bash
/remember I prefer TypeScript
# → inject_for: ["coding", "planning", "research"]

/remember I have two kids: Emma and Lucas
# → inject_for: ["planning", "research"]
```

### Phase 2: Memory Management & Filtering
**Features:**
- `/memory show coding` - Show only coding memories
- `/memory show personal` - Show only personal memories
- `/memory search <query>` - Keyword search
- `/memory edit <id>` - Edit memory content
- `/memory edit <id> --inject coding,planning` - Change which agents see it
- Tag-based organization

**Goal**: Full CRUD operations and better organization

### Phase 3: Implicit Learning
**Smart detection:**
- Detect patterns (e.g., "uses pytest 3 times")
- Ask user to confirm before saving
- Track `usage_count` and `confidence`
- Auto-assign `inject_for` based on detected pattern type

**Example:**
```
Athena: "I've noticed you always use pytest (3 times).
Should I remember this?"
User: "Yes"
Athena: ✓ Remembered: Prefers pytest
        → inject_for: ["coding", "planning"]
```

**Goal**: Automatic learning without manual input

### Phase 4: Advanced Memory Intelligence
**Features:**
- Memory staleness detection (update prompts for old preferences)
- Conflict resolution (handle contradicting memories)
- Confidence decay over time
- User can override `inject_for` per memory
- Memory suggestions during work

**Example:**
```
Athena: "I notice you're using Svelte, but I remember you
preferred React (6 months ago). Should I update this?"
```

**Goal**: Self-maintaining, intelligent system

### Phase 5: Cross-Agent Learning & Optimization
**Advanced features:**
- Track which memories actually helped each agent
- Optimize `inject_for` based on usage patterns
- Remove unused/unhelpful memories automatically (with user approval)
- Memory analytics: "Most useful memories", "Never used memories"

**Goal**: System that learns which memories are actually valuable

## Example Usage Scenarios

### Scenario 1: New User Onboarding

```
User: "My name is Sarah, I'm a data scientist"
Athena: ✓ Remembered: Name is Sarah, data scientist

User: "I prefer Python with type hints"
Athena: ✓ Remembered: Prefers Python with type hints

User: "Create a data pipeline"
Athena: "Hi Sarah! I'll create a Python data pipeline with type hints..."
```

### Scenario 2: Implicit Learning

```
Session 1: User asks to write Python code with pytest tests
Session 2: User asks to add tests, Athena writes pytest again
Session 3: User creates new project, asks for tests

Athena: "I've noticed you consistently use pytest for testing (3 times).
Should I remember this as your preferred testing framework?"

User: "Yes"
Athena: ✓ Remembered: Prefers pytest for testing

Session 4: User asks to add tests
Athena: [Automatically uses pytest without asking]
```

### Scenario 3: Agent-Aware Memory Usage

```
User: "/remember I have two kids: Emma (7) and Lucas (5)"
Athena: ✓ Remembered: Has two kids (Emma, Lucas)
        → inject_for: ["planning", "research"]

[Later session - Planning Agent]
User: "I want to build a simple game"
Planning Agent: "Since you have kids Emma (7) and Lucas (5), how about
an educational math game? I'll use TypeScript as you prefer, add pytest
tests, and make it kid-friendly with colorful animations."

[Same session - Coding Agent starts implementation]
Coding Agent: [Sees: TypeScript, pytest, functional style, NO personal context]
Coding Agent: "Let me implement the game with TypeScript..."
[Writes code without needing to know about Emma and Lucas]
```

**Key point**: Planning agent gets personal context for better suggestions,
coding agent stays focused on implementation without unnecessary context.

### Scenario 4: Memory Management

```
User: "/memory list"
Athena:
Personal (2):
  - mem_001: Name is Sarah, data scientist
  - mem_002: Has kids: Emma (7), Lucas (5)

Coding (3):
  - mem_003: Prefers Python with type hints
  - mem_004: Uses pytest for testing
  - mem_005: Prefers functional programming style

User: "/memory delete mem_005"
Athena: ✓ Deleted memory: Prefers functional programming style

User: "/memory show personal"
Athena:
Personal Memories:
  1. Name is Sarah, data scientist (explicit, 2026-01-09)
  2. Has kids: Emma (7), Lucas (5) (manual, 2026-01-09)
```

## Technical Considerations

### Storage Format
- **JSON** for simplicity and human-readability
- **Location**: `~/.athena/user_profile.json`
- **Backup**: Auto-backup to `~/.athena/user_profile.backup.json` on write

### Memory IDs
- Format: `mem_001`, `mem_002`, etc.
- Unique, sequential
- Never reused (even after deletion)

### Thread Safety
- Single-user tool, low concurrency risk
- File locking if needed (Python `fcntl`)

### Migration
- Version field in JSON for future schema changes
- Migration scripts for backwards compatibility

### Privacy
- Stored locally (never sent to external services)
- User can delete anytime
- Clear documentation about what's remembered

## Success Metrics

How do we know this is working?

1. **User doesn't repeat preferences**: No more "use TypeScript" every session
2. **Natural conversation flow**: Athena knows context without being told
3. **Relevant suggestions**: "This would be perfect for Emma and Lucas!"
4. **Time saved**: Less back-and-forth explaining preferences
5. **User trust**: Users actually use `/remember` and let Athena learn

## Risks & Mitigations

### Risk 1: Stale memories
**Problem**: User changes preferences, old memories cause wrong behavior
**Mitigation**: Confidence decay, update detection, easy deletion

### Risk 2: Privacy concerns
**Problem**: Users uncomfortable with "being remembered"
**Mitigation**: Transparent, local storage, easy to view/delete, opt-in for implicit

### Risk 3: False patterns
**Problem**: Athena learns incorrect patterns from limited data
**Mitigation**: Require confirmation for implicit, high confidence threshold, easy correction

### Risk 4: Context bloat
**Problem**: 100+ memories make prompt too large
**Mitigation**: Hybrid approach (always inject + retrieve), confidence filtering

### Risk 5: Conflicting memories
**Problem**: Multiple contradictory preferences stored
**Mitigation**: Timestamp priority, specificity rules, ask user when unclear

## Future Enhancements (Out of Scope for v1)

- **Project-specific memories**: `.athena/project_memory.json`
- **Memory sharing**: Export/import (if requested later)
- **Memory analytics**: "Most used memories", "Memory effectiveness"
- **Voice/personality**: Remember communication style preferences
- **Collaboration memories**: "Works with teammate Bob on API design"
- **Learning from mistakes**: "Don't use X because it caused bugs last time"

---

## Feedback Needed

Please review and provide thoughts on:

1. **Agent-aware approach** - Does the `inject_for` field make sense? Is filtering by agent type the right approach?
2. **Memory structure** - Does the JSON format with agent awareness work?
3. **Auto-detection of inject_for** - Should coding prefs go to all agents? Personal only to planning/research?
4. **Implicit learning** - Detection after 3 instances? Too aggressive/conservative?
5. **Memory visibility** - Should Athena mention when using memories?
6. **Staleness handling** - How to deal with outdated preferences?
7. **Slash commands** - Are the proposed commands intuitive?
8. **Phase 1 scope** - Is "manual memory + agent-aware injection" a good start?
9. **User override** - Should users be able to manually set `inject_for` per memory?
10. **Any missing use cases** - What else should be remembered?

## Key Design Decisions Made

✅ **Agent-aware memory injection** - Different agents see different memories
✅ **No RAG/retrieval** - Simple filtering by agent type, no semantic search
✅ **System prompt injection** - All relevant memories injected into system prompt
✅ **Token efficient** - Coding agents ~150 tokens, planning agents ~250 tokens
✅ **Personal context for planning only** - Helps with relevant suggestions

---

**Created**: 2026-01-09
**Updated**: 2026-01-10 (Added agent-aware approach)
**Status**: Draft - awaiting feedback
**Next Step**: Review with friend, gather feedback, refine design
