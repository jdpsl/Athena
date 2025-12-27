# Athena Quick Start Guide

Get up and running with Athena in 5 minutes!

## Prerequisites

- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **LM Studio** or any OpenAI-compatible API ([LM Studio Download](https://lmstudio.ai/))

## Installation

### 1. Install Athena

```bash
cd athena
pip install -e .
```

### 2. Start Athena

```bash
athena
```

You should see:
```
╭─────────────────────────────────────────╮
│      Athena AI                          │
│ Open-source AI agent for coding         │
│ Type /help for commands, /exit to quit  │
╰─────────────────────────────────────────╯
```

### 3. Configure Athena (First Time Setup)

```bash
You: /api http://localhost:1234/v1
✓ API base set to: http://localhost:1234/v1

You: /apikey not-needed
✓ API key set

You: /model local-model
✓ Model set to: local-model

You: /temp 0.5
✓ Temperature set to: 0.5

You: /fallback on
✓ Fallback mode enabled
  Using text-based tool calling (TOOL[Name]{args})

You: /save
✓ Settings saved to ~/.athena/config.json
```

**Done!** Settings are now saved and will load automatically next time.

## Using with LM Studio

### Setup LM Studio

1. **Download LM Studio** from https://lmstudio.ai/

2. **Download a model:**
   - Recommended for beginners: `Llama-3.2-3B-Instruct`
   - For better results: `Llama-3.1-8B-Instruct` or larger
   - Advanced: `Hermes-3-Llama-3.1-8B` (has native function calling)

3. **Start the server:**
   - Open LM Studio
   - Go to **"Local Server"** tab
   - Click **"Start Server"**
   - Default port is `1234`

4. **Configure Athena:**

   ```bash
   athena

   You: /api http://localhost:1234/v1
   You: /fallback on
   You: /save
   ```

5. **Test it:**
   ```bash
   You: What is Python?
   ```

   If you get a response, you're all set! 🎉

## Important: Fallback Mode

**Most local models need fallback mode enabled!**

If you see this error:
```
error code: 400 - {'code': 'client specified an invalid argument','error':'invalid request content...
```

**Solution:**
```bash
You: /fallback on
```

### What is Fallback Mode?

- **Problem:** Most local models don't support OpenAI-style function calling
- **Solution:** Athena teaches the model to use text-based tool calls
- **Format:** `TOOL[ToolName]{"param": "value"}`
- **Result:** Works with ANY model!

### When to use fallback mode:

✅ **USE FALLBACK MODE** for:
- Llama models (3, 3.1, 3.2, etc.)
- Mistral base models
- Qwen, Phi, Gemma models
- Most models in LM Studio
- If you get JSON/400 errors

❌ **DON'T USE** for:
- OpenAI GPT-4, GPT-3.5
- Hermes-2-Pro, Hermes-3 (they have native function calling)
- Functionary models
- Claude API (via third-party)

## Quick Usage Examples

### Basic Tasks

```bash
You: Create a Python file called hello.py that prints "Hello, World!"

You: Read the file app.py

You: List all Python files in the current directory

You: Search for the word "TODO" in all files
```

### File Operations

```bash
You: Create a new directory called "tests"

You: Copy app.py to backup/app.py

You: Delete all .pyc files

You: Move old.py to archive/old.py
```

### Git Operations

```bash
You: Check git status

You: Show me what changed in my files

You: Create a commit with message "Add new feature"

You: Switch to a new branch called feature-login
```

### Web Research

```bash
You: Search the web for "Python asyncio tutorial"

You: Fetch the documentation from https://docs.python.org/3/
```

### Complex Tasks

```bash
You: Create a Flask web app with a hello world endpoint

You: Review this code for security issues

You: Write unit tests for the calculate_total function
```

## Built-in Commands Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/exit` | Exit Athena |
| `/clear` | Clear conversation history |

### Configuration Commands

| Command | Example | Description |
|---------|---------|-------------|
| `/config` | - | Show current settings |
| `/model [name]` | `/model gpt-4` | Set model name |
| `/api [url]` | `/api http://localhost:1234/v1` | Set API endpoint |
| `/apikey [key]` | `/apikey sk-123...` | Set API key |
| `/temp [value]` | `/temp 0.5` | Set temperature (0.0-1.0) |
| `/fallback [on\|off]` | `/fallback on` | Toggle fallback mode |
| `/save` | - | Save settings to `~/.athena/config.json` |

### Information Commands

| Command | Description |
|---------|-------------|
| `/tools` | List all 21 available tools |
| `/commands` | List custom slash commands |

## Available Tools (21 Total)

### File Operations
- `Read` - Read files with line numbers
- `Write` - Create or overwrite files
- `Edit` - Make precise string replacements
- `DeleteFile` - Delete files/directories (safe)
- `MoveFile` - Move or rename files
- `CopyFile` - Copy files/directories
- `ListDir` - List directory contents
- `MakeDir` - Create directories

### Search
- `Glob` - Find files by pattern (`**/*.py`)
- `Grep` - Search file contents

### Git
- `GitStatus` - Repository status
- `GitDiff` - View changes
- `GitCommit` - Create commits
- `GitLog` - View history
- `GitBranch` - Manage branches

### Execution
- `Bash` - Run shell commands

### Web
- `WebSearch` - Search the internet
- `WebFetch` - Fetch web pages

### Other
- `TodoWrite` - Track task progress
- `Task` - Spawn specialized sub-agents
- `AskUserQuestion` - Ask for clarification

## Creating Custom Commands

Custom commands let you create reusable prompts.

### Example: Code Review Command

1. **Create the command file:**
   ```bash
   mkdir -p ~/.athena/commands
   nano ~/.athena/commands/review.md
   ```

2. **Add your prompt:**
   ```markdown
   Review the code for:
   - Security vulnerabilities (SQL injection, XSS, CSRF)
   - Performance issues
   - Code quality and best practices
   - Potential bugs
   - Missing error handling

   Provide specific suggestions for improvement.
   ```

3. **Use it:**
   ```bash
   You: /review
   ```

### More Command Examples

**Debug Helper** (`~/.athena/commands/debug.md`):
```markdown
Help me debug this code:
1. Identify potential issues
2. Suggest fixes
3. Explain why the issues occur
```

**Test Generator** (`~/.athena/commands/test.md`):
```markdown
Generate comprehensive unit tests for the current code.
Include:
- Happy path tests
- Edge cases
- Error handling tests
- Mock external dependencies
```

**Documentation** (`~/.athena/commands/document.md`):
```markdown
Generate documentation for this code including:
- Function/class descriptions
- Parameter explanations
- Return value descriptions
- Usage examples
- Any important notes or warnings
```

## Tips for Best Results

### 1. Use Lower Temperature for Tool Usage
```bash
/temp 0.3
```
Lower temperature = more reliable tool calls

### 2. Enable Fallback Mode for Local Models
```bash
/fallback on
```
Most local models need this!

### 3. Let Athena Read Before Editing
```bash
You: Read app.py then fix the bug on line 42
```
Reading first improves accuracy

### 4. Clear Context Periodically
```bash
/clear
```
Reduces context size for faster responses

### 5. Save Your Configuration
```bash
/save
```
Never configure again!

## Recommended Settings by Model Type

### Local Models (LM Studio)
```bash
/api http://localhost:1234/v1
/model local-model
/temp 0.4
/fallback on
/save
```

### OpenAI
```bash
/api https://api.openai.com/v1
/apikey sk-your-key-here
/model gpt-4
/temp 0.5
/fallback off
/save
```

### Groq (Fast!)
```bash
/api https://api.groq.com/openai/v1
/apikey gsk-your-key-here
/model llama-3.1-70b-versatile
/temp 0.3
/fallback on
/save
```

### Hermes Models (Best for Function Calling)
```bash
/api http://localhost:1234/v1
/model hermes-3-llama-3.1-8b
/temp 0.5
/fallback off  # Hermes has native function calling!
/save
```

## Troubleshooting

### ❌ Problem: "Invalid JSON" or 400 errors
**Solution:**
```bash
/fallback on
```
Your model doesn't support function calling.

---

### ❌ Problem: "Connection refused"
**Solution:**
1. Check LM Studio is running
2. Verify server is started (Local Server tab)
3. Check port: `/api http://localhost:1234/v1`
4. Test: `curl http://localhost:1234/v1/models`

---

### ❌ Problem: "Python version not compatible"
**Solution:**
```bash
# Check version
python3 --version

# Install Python 3.10+ (macOS)
brew install python@3.11

# Install Python 3.10+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11

# Then reinstall Athena
python3.11 -m pip install -e .
```

---

### ❌ Problem: Athena not responding
**Solution:**
1. Check model is loaded in LM Studio
2. Lower temperature: `/temp 0.3`
3. Try a different model
4. Check LM Studio logs for errors

---

### ❌ Problem: Responses are cut off
**Solution:**
Add to `config.yaml`:
```yaml
llm:
  max_tokens: 4096  # Increase token limit
```

---

### ❌ Problem: Very slow responses
**Solution:**
1. Use a smaller model (7B instead of 70B)
2. Clear context: `/clear`
3. Try Groq for fast inference
4. Reduce `max_tokens` if set very high

---

## Example Session

Here's a complete example session:

```bash
$ athena

╭─────────────────────────────────────────╮
│      Athena AI                          │
│ Open-source AI agent for coding         │
│ Type /help for commands, /exit to quit  │
╰─────────────────────────────────────────╯

You: /fallback on
✓ Fallback mode enabled
  Using text-based tool calling (TOOL[Name]{args})

You: Create a Python script that reads a CSV file and prints the total of a 'price' column

Athena:
→ Iteration 1/50

💭 I'll create a Python script that uses the csv module to read a CSV file and calculate the sum of the price column...

🔧 Tool: Write(...)

I've created a script called read_csv.py that:
- Reads a CSV file using the csv.DictReader
- Sums all values in the 'price' column
- Handles errors gracefully
- Prints the total

To use it:
```bash
python read_csv.py data.csv
```

The script expects a CSV file with a 'price' column.

You: Now add error handling for non-numeric prices

Athena:
→ Iteration 1/50

🔧 Tool: Edit(...)

✓ Updated the script to:
- Skip non-numeric values with a warning
- Handle missing 'price' column
- Show count of valid/invalid entries
- Use try-except for float conversion

The script now safely handles malformed data.

You: Perfect! /exit

Goodbye!
```

## Next Steps

Now that you're set up:

1. ✅ **Try it out:** Ask Athena to help with a real coding task
2. 📖 **Read the README:** Learn about all 21 tools and features
3. ⚙️ **Create custom commands:** Set up your workflow
4. 🔧 **Experiment:** Try different models and temperatures
5. 💾 **Save your config:** Use `/save` to persist your setup

## Getting Help

- **In Athena:** Type `/help`
- **Documentation:** Read the full `README.md`
- **Examples:** Check `.athena/commands/*.md` files
- **Issues:** Report bugs on GitHub

## Quick Reference Card

```bash
# First Time Setup
athena                    # Start Athena
/api <url>               # Set API endpoint
/apikey <key>            # Set API key
/fallback on             # Enable for local models
/save                    # Save settings

# Common Tasks
You: Read app.py
You: Create a file called test.py
You: Check git status
You: Search the web for "topic"

# Commands
/help                    # Show all commands
/config                  # Show settings
/clear                   # Clear history
/exit                    # Quit

# Configuration
/model <name>            # Change model
/temp <0.0-1.0>         # Set temperature
/fallback on|off        # Toggle fallback mode
/save                    # Save config
```

Happy coding with Athena! 🚀
