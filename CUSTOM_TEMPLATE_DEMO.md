# Custom Template Demo: How It Works

This document demonstrates Athena's custom template system with a real working example.

## What Was Created

### 1. Example Custom Template

A complete **Python Discord Bot** template in `~/.athena/templates/`:

```
~/.athena/templates/python/discord-bot/
├── structure.yaml          # Template definition
├── README.md              # Project documentation template
├── bot.py                 # Discord bot main file
├── config.py              # Configuration with Pydantic
├── cog_general.py         # General commands (ping, hello, serverinfo)
├── cog_admin.py           # Admin commands (kick, ban, slowmode)
├── pyproject.toml         # Python project configuration
├── .env.example           # Environment variables example
├── test_bot.py            # Pytest tests
└── test-workflow.yml      # GitHub Actions CI/CD
```

### 2. How Athena Discovers It

**Automatic Discovery** - No configuration needed!

1. User asks: "Create a python-discord-bot project called my-bot"
2. Athena extracts template type: `python-discord-bot`
3. Searches for templates:
   - **First**: `~/.athena/templates/python/discord-bot/structure.yaml` ← **Found!**
   - Second: `athena/templates/python/discord-bot/structure.yaml`
4. Loads the first match and creates the project

### 3. What Gets Generated

When you run:
```
Athena: Create a python-discord-bot project called "my-bot" for managing my community
```

Athena creates:

```
my-bot/
├── my_bot/                    # Main package
│   ├── __init__.py            # Package init with version
│   ├── bot.py                 # Discord bot with event handlers
│   ├── config.py              # Settings from environment variables
│   └── cogs/                  # Command modules
│       ├── general.py         # /ping, /hello, /serverinfo, /userinfo
│       └── admin.py           # /kick, /ban, /clear, /slowmode
├── tests/                     # Test suite
│   ├── __init__.py
│   └── test_bot.py            # Pytest tests
├── .github/workflows/         # CI/CD
│   └── test.yml               # Run tests on push
├── README.md                  # Complete documentation
├── pyproject.toml             # Dependencies and metadata
├── .env.example               # Environment configuration template
├── .gitignore                 # Python gitignore
└── LICENSE                    # MIT License
```

**All with proper variable substitution!**

---

## Live Demo

### Step 1: List Available Templates

```python
from athena.templates.loader import TemplateLoader

loader = TemplateLoader()
templates = loader.list_templates()

for t in templates:
    print(f"• {t['type']}: {t['name']}")
```

**Output:**
```
• python-web: Python Web API
• node-web: Node.js Web API
• python-discord-bot: Python Discord Bot  ← Custom template!
```

### Step 2: Create a Project

```python
import asyncio
from athena.tools.initialize_project import InitializeProjectTool

async def create_bot():
    tool = InitializeProjectTool()
    result = await tool.execute(
        project_type='python-discord-bot',
        project_name='community-bot',
        description='A Discord bot for managing my gaming community',
        author='Jane Doe',
        email='jane@example.com',
        license='MIT',
        init_git=False
    )
    print(result.output)

asyncio.run(create_bot())
```

**Output:**
```
✅ Project initialized: community-bot
📁 Type: Python Discord Bot

📦 Created structure:
  ✓ community_bot/
  ✓ community_bot/cogs/
  ✓ tests/
  ✓ .github/workflows/

📝 Generated files:
  ✓ README.md
  ✓ pyproject.toml
  ✓ .gitignore
  ✓ LICENSE
  ✓ .env.example
  ✓ community_bot/__init__.py
  ✓ community_bot/bot.py
  ✓ community_bot/config.py
  ✓ community_bot/cogs/general.py
  ✓ community_bot/cogs/admin.py
  ... and 3 more files

🚀 Next steps:
  1. cd community-bot
  2. python -m venv venv
  3. source venv/bin/activate
  4. pip install -e ".[dev]"
  5. cp .env.example .env
  6. # Add your Discord bot token to .env
  7. python -m community_bot.bot
```

### Step 3: Check Generated Content

**README.md** (with variables substituted):
```markdown
# community-bot

A Discord bot for managing my gaming community

A Discord bot built with discord.py featuring slash commands, cogs, and modern Python best practices.

## Features

- Discord.py 2.0+ with slash commands
- Modular cog system for organizing commands
...

## Author

Jane Doe <jane@example.com>

## License

MIT
```

**bot.py** (with proper imports):
```python
"""community-bot - Discord Bot

Main bot initialization and event handlers.
"""

import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from community_bot.config import settings  # ← Correct snake_case import!

# ... rest of bot code
```

**pyproject.toml** (with metadata):
```toml
[project]
name = "community-bot"
version = "0.1.0"
description = "A Discord bot for managing my gaming community"
authors = [
    {name = "Jane Doe", email = "jane@example.com"}
]
license = {text = "MIT"}

dependencies = [
    "discord.py>=2.3.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]
```

---

## How Athena Knows About Custom Templates

### 1. Built-in Discovery

The `TemplateLoader` class automatically checks **two locations**:

```python
def __init__(self, template_dir: Optional[Path] = None):
    # System templates (built-in)
    self.template_dir = Path(__file__).parent

    # User templates (custom)
    self.user_template_dir = Path.home() / ".athena" / "templates"
```

### 2. Priority: User Templates First

When loading templates, Athena checks in this order:

```python
def load_template(self, template_type: str) -> Optional[ProjectTemplate]:
    # Check user templates first (allows override)
    for base_dir in [self.user_template_dir, self.template_dir]:
        structure_file = self._find_template_structure(base_dir, template_type)
        if structure_file:
            return self._load_structure_yaml(structure_file)

    return None
```

This means:
- **Custom templates override system templates** with the same name
- You can customize `python-web` by creating `~/.athena/templates/python/web/`
- Perfect for company-specific standards!

### 3. Template Type Mapping

Template type → Directory path:

```python
def _find_template_structure(self, base_dir: Path, template_type: str) -> Optional[Path]:
    parts = template_type.split("-")
    if len(parts) >= 2:
        language = parts[0]
        project_type = "-".join(parts[1:])  # Join remaining parts
        structure_file = base_dir / language / project_type / "structure.yaml"
        if structure_file.exists():
            return structure_file
    return None
```

Examples:
- `python-web` → `python/web/structure.yaml`
- `python-discord-bot` → `python/discord-bot/structure.yaml`
- `node-express-api` → `node/express-api/structure.yaml`

### 4. Listing Templates

The `list_templates()` method scans **both directories**:

```python
def list_templates(self) -> List[Dict[str, str]]:
    templates = []

    # Check both system and user templates
    for base_dir in [self.template_dir, self.user_template_dir]:
        if not base_dir.exists():
            continue

        # Find all structure.yaml files
        for structure_file in base_dir.rglob("structure.yaml"):
            try:
                template = self._load_structure_yaml(structure_file)
                templates.append({
                    "name": template.name,
                    "type": template.type,
                    "description": template.description,
                    "path": str(structure_file.parent)
                })
            except Exception:
                pass  # Skip invalid templates

    return templates
```

**Result**: All templates from both locations appear in the list automatically!

---

## Key Features Demonstrated

### 1. Zero Configuration

- No need to register templates
- No configuration files to edit
- Just drop files in `~/.athena/templates/` and they work!

### 2. Template Reuse

Custom templates can reference system templates:

```yaml
files:
  # Use custom template
  - path: "bot.py"
    template: "bot.py"

  # Reuse system .gitignore
  - path: ".gitignore"
    template: "python/.gitignore"

  # Reuse system LICENSE
  - path: "LICENSE"
    template: "base/LICENSE.{{license}}"
```

### 3. Variable Substitution

All variables work everywhere:

```yaml
# In file paths
- path: "{{project_name_snake}}/main.py"

# In template content
"""{{project_name}} - {{description}}"""
__author__ = "{{author}}"

# In next steps
next_steps:
  - "cd {{project_name}}"
  - "python -m {{project_name_snake}}.main"
```

### 4. Template Override

System templates can be overridden:

```bash
# Create custom version of python-web
mkdir -p ~/.athena/templates/python/web
cp athena/templates/python/web/structure.yaml ~/.athena/templates/python/web/
# Edit structure.yaml with your company's standards
```

Now your custom `python-web` template will be used instead of the system one!

---

## Bug Fixes Included

### 1. Multi-Word Template Types

**Before** (broken):
```python
# python-discord-bot split into ["python", "discord", "bot"]
language = parts[0]      # "python"
project_type = parts[1]  # "discord" ← Wrong! Missing "bot"
# Looked for: python/discord/structure.yaml ✗
```

**After** (fixed):
```python
# python-discord-bot split into ["python", "discord", "bot"]
language = parts[0]              # "python"
project_type = "-".join(parts[1:])  # "discord-bot" ← Correct!
# Looks for: python/discord-bot/structure.yaml ✓
```

### 2. Error Handling

**Before** (broken):
```python
return ToolResult(
    success=False,
    error=f"Template not found"  # ToolResult has no 'error' field!
)
```

**After** (fixed):
```python
return ToolResult(
    success=False,
    output=f"❌ Template not found"  # Use 'output' field
)
```

---

## Documentation Created

### 1. TEMPLATE_ROADMAP.md

Complete roadmap of 29 planned templates:
- **Phase 1**: Fix broken templates (python-cli, python-lib, node-cli)
- **Phase 2**: Critical frontend (React, Next.js)
- **Phase 3**: Popular backend (Django, Flask, NestJS)
- **Phase 4**: Specialized (Data Science, Full-stack, Vue, Rust, Go)
- **Phase 5**: Extended ecosystem (15 more templates)

Includes competitive analysis vs Claude Code showing Athena's advantages.

### 2. CUSTOM_TEMPLATES_GUIDE.md

Comprehensive 1000+ line guide covering:
- Quick start (4 steps to create a template)
- Template structure explanation
- Full tutorial creating a Discord bot template
- Template variables reference
- How Athena discovers templates
- Advanced features (inline content, conditionals, sharing)
- Best practices (10 guidelines)
- Troubleshooting (7 common issues + solutions)
- Real examples (Python CLI, React TypeScript)

---

## Summary

### What You Get

1. **Custom Templates** - Create your own project templates in `~/.athena/templates/`
2. **Automatic Discovery** - Athena finds them automatically, no configuration
3. **Override System Templates** - Customize built-in templates for your needs
4. **Company Standards** - Perfect for enforcing team/company conventions
5. **Template Reuse** - Reference system templates from custom templates
6. **Variable Substitution** - Full variable support in paths and content
7. **Priority System** - User templates override system templates

### How Athena Uses Them

1. User requests a project type
2. Athena checks `~/.athena/templates/` first
3. Falls back to system templates if not found
4. Loads template and renders with variables
5. Creates complete project structure
6. Shows next steps to user

### No Configuration Needed!

- No files to edit
- No settings to change
- No registration required
- Just create `~/.athena/templates/language/type/structure.yaml` and go!

---

## Try It Yourself

```bash
# 1. Create your first custom template
mkdir -p ~/.athena/templates/python/mytemplate
cd ~/.athena/templates/python/mytemplate

# 2. Create structure.yaml
cat > structure.yaml << 'EOF'
name: "My Custom Template"
type: "python-mytemplate"
description: "My awesome custom template"

directories:
  - "{{project_name_snake}}"

files:
  - path: "README.md"
    content: '# {{project_name}}

{{description}}

Author: {{author}}
'

next_steps:
  - "cd {{project_name}}"
  - "# Start building!"
EOF

# 3. Test it!
# Just ask Athena: "Create a python-mytemplate project called test"
```

**That's it!** Your custom template is ready to use. 🚀

---

For detailed guidance, see [CUSTOM_TEMPLATES_GUIDE.md](CUSTOM_TEMPLATES_GUIDE.md)
For template ideas, see [TEMPLATE_ROADMAP.md](TEMPLATE_ROADMAP.md)
