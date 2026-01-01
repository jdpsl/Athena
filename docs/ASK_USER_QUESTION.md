# AskUserQuestion Tool - Multiple Choice Support

**Status:** ✅ Implemented
**Date:** 2025-12-28
**Compatibility:** Claude Code format compatible

## Overview

The `AskUserQuestion` tool allows agents to ask users questions with optional multiple-choice options. Users can select from predefined options OR provide their own custom answer.

## Features

- ✅ **Simple text questions** (backward compatible)
- ✅ **Multiple choice** with 2-4 predefined options per question
- ✅ **Automatic "Other" option** - users can always provide custom answers
- ✅ **Multi-select support** - choose multiple options
- ✅ **Up to 4 questions** per tool call
- ✅ **Rich UI** with headers, descriptions, and formatting
- ✅ **Claude Code compatible** - same format as Claude Code's implementation

## Usage

### Format 1: Simple Question (Backward Compatible)

```python
AskUserQuestion(
    question="What port should the server run on?",
    context="We need to choose a port for the development server"
)
```

**User sees:**
```
╭─────────────────────────────────────────────╮
│ Question from Athena                        │
│                                             │
│ We need to choose a port for the           │
│ development server                          │
│                                             │
│ What port should the server run on?         │
╰─────────────────────────────────────────────╯

Your answer: _
```

### Format 2: Multiple Choice (Single Selection)

```python
AskUserQuestion(
    questions=[
        {
            "question": "Which database should we use?",
            "header": "DB Choice",
            "options": [
                {
                    "label": "PostgreSQL",
                    "description": "Powerful relational database"
                },
                {
                    "label": "MongoDB",
                    "description": "NoSQL with flexible schema"
                },
                {
                    "label": "SQLite",
                    "description": "Lightweight embedded database"
                }
            ],
            "multiSelect": False
        }
    ]
)
```

**User sees:**
```
╭─────────────────────────────────────────────╮
│ Question from Athena                        │
│                                             │
│ Which database should we use?               │
│  DB Choice                                  │
│                                             │
│  1.  PostgreSQL                             │
│      Powerful relational database           │
│                                             │
│  2.  MongoDB                                │
│      NoSQL with flexible schema             │
│                                             │
│  3.  SQLite                                 │
│      Lightweight embedded database          │
│                                             │
│  4.  Other                                  │
│      Provide your own answer                │
╰─────────────────────────────────────────────╯

Your choice (1-4 or custom text): _
```

**User can:**
- Type `1` to select PostgreSQL
- Type `2` to select MongoDB
- Type `3` to select SQLite
- Type `4` to provide custom answer
- Type `Redis` directly for custom answer

### Format 3: Multiple Choice (Multi-Selection)

```python
AskUserQuestion(
    questions=[
        {
            "question": "Which features should we implement?",
            "header": "Features",
            "options": [
                {
                    "label": "User Authentication",
                    "description": "Login and session management"
                },
                {
                    "label": "API Endpoints",
                    "description": "RESTful API for data access"
                },
                {
                    "label": "Admin Dashboard",
                    "description": "Management interface"
                }
            ],
            "multiSelect": True
        }
    ]
)
```

**User can:**
- Type `1,2` to select Authentication + API
- Type `1,2,3` to select all three
- Type `1,4` and be prompted for custom answer
- Type custom text directly

### Format 4: Multiple Questions

```python
AskUserQuestion(
    questions=[
        {
            "question": "Which framework?",
            "header": "Framework",
            "options": [
                {"label": "FastAPI", "description": "Modern async"},
                {"label": "Flask", "description": "Lightweight"}
            ],
            "multiSelect": False
        },
        {
            "question": "Which authentication method?",
            "header": "Auth",
            "options": [
                {"label": "JWT", "description": "Stateless tokens"},
                {"label": "Sessions", "description": "Server-side"}
            ],
            "multiSelect": False
        }
    ]
)
```

## Parameters

### Simple Format

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | The question to ask |
| `context` | string | No | Optional context to help user understand |

### Multiple Choice Format

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `questions` | array | Yes | Array of 1-4 question objects |

**Question Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The question text |
| `header` | string | No | Short label (max 12 chars) shown as tag |
| `options` | array | Yes | Array of 2-4 option objects |
| `multiSelect` | boolean | No | Allow multiple selections (default: false) |

**Option Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Display text (1-5 words, concise) |
| `description` | string | Yes | Explanation of what this option means |

## Constraints

- **Questions per call:** 1-4
- **Options per question:** 2-4 (plus automatic "Other")
- **Header length:** Max 12 characters
- **Label length:** 1-5 words (concise)

## Return Value

**Simple format:**
```python
ToolResult(
    success=True,
    output="User answered: 3000",
    metadata={"question": "...", "answer": "3000"}
)
```

**Multiple choice format:**
```python
ToolResult(
    success=True,
    output="Q: Which database?\nA: PostgreSQL",
    metadata={
        "answers": {
            "Which database?": "PostgreSQL"
        }
    }
)
```

**Multi-select format:**
```python
ToolResult(
    success=True,
    output="Q: Which features?\nA: User Authentication, API Endpoints",
    metadata={
        "answers": {
            "Which features?": ["User Authentication", "API Endpoints"]
        }
    }
)
```

## Examples

### Example 1: Database Selection

```python
# Agent asks
AskUserQuestion(
    questions=[{
        "question": "Which database should we use for user data?",
        "header": "Database",
        "options": [
            {"label": "PostgreSQL", "description": "Best for relational data"},
            {"label": "MongoDB", "description": "Best for flexible schemas"},
            {"label": "Redis", "description": "Best for caching"}
        ],
        "multiSelect": False
    }]
)

# User selects: 1
# Agent receives: "PostgreSQL"
```

### Example 2: Feature Prioritization

```python
# Agent asks
AskUserQuestion(
    questions=[{
        "question": "Which features are most important?",
        "header": "Priority",
        "options": [
            {"label": "Performance", "description": "Fast response times"},
            {"label": "Security", "description": "Strong authentication"},
            {"label": "Usability", "description": "Easy to use interface"}
        ],
        "multiSelect": True
    }]
)

# User selects: 1,2
# Agent receives: ["Performance", "Security"]
```

### Example 3: Custom Answer

```python
# Agent asks
AskUserQuestion(
    questions=[{
        "question": "What should the API rate limit be?",
        "header": "Rate Limit",
        "options": [
            {"label": "100/hour", "description": "Conservative limit"},
            {"label": "1000/hour", "description": "Standard limit"}
        ],
        "multiSelect": False
    }]
)

# User types: 500/hour per user
# Agent receives: "500/hour per user"
```

## When to Use

**Use multiple choice when:**
- There are 2-4 obvious good choices
- You want to guide the user toward best practices
- You need quick decisions without long explanations

**Use simple questions when:**
- The answer is open-ended
- There are too many possible options
- You need detailed explanations

**Use multi-select when:**
- User might want multiple options
- Choices are not mutually exclusive
- You're prioritizing features/tasks

## Backward Compatibility

The tool is **100% backward compatible**. Existing code using simple questions continues to work:

```python
# Old code (still works)
AskUserQuestion(question="What should the timeout be?")

# New code (also works)
AskUserQuestion(
    questions=[{
        "question": "What should the timeout be?",
        "header": "Timeout",
        "options": [
            {"label": "30s", "description": "Standard"},
            {"label": "60s", "description": "Extended"}
        ]
    }]
)
```

## Testing

Run the interactive demo:

```bash
cd ~/testing
python3 test_ask_user_question.py
```

This demonstrates all formats and features.

## Comparison with Claude Code

| Feature | Claude Code | Athena | Compatible |
|---------|-------------|--------|------------|
| Multiple choice | ✅ | ✅ | ✅ |
| Auto "Other" option | ✅ | ✅ | ✅ |
| Multi-select | ✅ | ✅ | ✅ |
| 1-4 questions | ✅ | ✅ | ✅ |
| 2-4 options | ✅ | ✅ | ✅ |
| Header tag | ✅ | ✅ | ✅ |
| Option descriptions | ✅ | ✅ | ✅ |
| Simple questions | ❌ | ✅ | ✅ Better |

**Athena adds:**
- Backward compatibility with simple text questions
- Works without breaking existing code

## Implementation Details

**File:** `athena/tools/user_interaction.py`

**Key Methods:**
- `_execute_simple()` - Handles backward-compatible simple questions
- `_execute_multiple_choice()` - Handles new multiple-choice format
- `_show_question_with_options()` - Displays rich UI with options

**UI Library:** Rich (tables, panels, formatting)

## Future Enhancements

Possible improvements:
- [ ] Recommended option indicator (show which option is recommended)
- [ ] Keyboard shortcuts (arrow keys to select)
- [ ] Search/filter for long option lists
- [ ] Conditional questions (ask Q2 based on Q1 answer)
- [ ] Validation rules (require at least N selections)

## References

- Claude Code AskUserQuestion (undocumented, reverse-engineered)
- [GitHub Issue #10346](https://github.com/anthropics/claude-code/issues/10346) - Documentation request
