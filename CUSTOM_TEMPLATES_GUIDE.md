# Custom Templates Guide

Learn how to create your own project templates for Athena's project initialization system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Template Structure](#template-structure)
3. [Creating Your First Template](#creating-your-first-template)
4. [Template Variables](#template-variables)
5. [How Athena Finds Templates](#how-athena-finds-templates)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Create Template Directory

```bash
mkdir -p ~/.athena/templates/language/project-type
```

Example for a Python Discord bot:
```bash
mkdir -p ~/.athena/templates/python/discord-bot
```

### 2. Create structure.yaml

This file defines your template structure:

```yaml
name: "Python Discord Bot"
type: "python-discord-bot"  # Must match directory path (language-project-type)
description: "Discord bot with discord.py, slash commands, and cogs"

directories:
  - "{{project_name_snake}}"
  - "tests"

files:
  - path: "README.md"
    template: "README.md"
  - path: "LICENSE"
    template: "base/LICENSE.{{license}}"

dependencies:
  main:
    - "discord.py>=2.3.0"
  dev:
    - "pytest>=7.4.0"

next_steps:
  - "cd {{project_name}}"
  - "pip install -e \".[dev]\""
```

### 3. Create Template Files

Create your template files in the same directory as `structure.yaml`:

```bash
~/.athena/templates/python/discord-bot/
├── structure.yaml
├── README.md
├── bot.py
├── config.py
└── test_bot.py
```

### 4. Use Your Template

Athena automatically discovers your template:

```
User: Create a python-discord-bot project called "my-bot"
```

That's it! Athena will find and use your custom template.

---

## Template Structure

### Directory Layout

```
~/.athena/templates/
├── python/
│   ├── discord-bot/        # python-discord-bot template
│   │   ├── structure.yaml
│   │   ├── README.md
│   │   ├── bot.py
│   │   └── config.py
│   ├── flask-app/          # python-flask-app template
│   │   ├── structure.yaml
│   │   └── ...
│   └── ...
├── node/
│   ├── express-api/        # node-express-api template
│   │   ├── structure.yaml
│   │   └── ...
│   └── ...
└── rust/
    ├── cli/                # rust-cli template
    │   ├── structure.yaml
    │   └── ...
    └── ...
```

### Template Type Naming

The template type MUST follow this pattern:

```
Template Type = language-project-type
Directory Path = ~/.athena/templates/language/project-type/
```

Examples:
- `python-web` → `~/.athena/templates/python/web/`
- `python-discord-bot` → `~/.athena/templates/python/discord-bot/`
- `node-express-api` → `~/.athena/templates/node/express-api/`
- `rust-cli` → `~/.athena/templates/rust/cli/`

---

## Creating Your First Template

Let's create a complete Python Discord bot template from scratch.

### Step 1: Create Directory

```bash
mkdir -p ~/.athena/templates/python/discord-bot
cd ~/.athena/templates/python/discord-bot
```

### Step 2: Create structure.yaml

```yaml
name: "Python Discord Bot"
type: "python-discord-bot"
description: "Discord bot with discord.py, slash commands, and cogs"

# Directories to create
directories:
  - "{{project_name_snake}}"
  - "{{project_name_snake}}/cogs"
  - "tests"
  - ".github/workflows"

# Files to generate
files:
  # README with template file
  - path: "README.md"
    template: "README.md"

  # Config file with template
  - path: "pyproject.toml"
    template: "pyproject.toml"

  # Inline content (no template file needed)
  - path: "{{project_name_snake}}/__init__.py"
    content: '"""{{project_name}} - {{description}}"""

__version__ = "0.1.0"
'

  # Main bot file
  - path: "{{project_name_snake}}/bot.py"
    template: "bot.py"

  # Reference shared templates
  - path: ".gitignore"
    template: "python/.gitignore"

  - path: "LICENSE"
    template: "base/LICENSE.{{license}}"

# Dependencies (for documentation)
dependencies:
  main:
    - "discord.py>=2.3.0"
    - "python-dotenv>=1.0.0"
  dev:
    - "pytest>=7.4.0"
    - "ruff>=0.1.0"

# Next steps shown to user
next_steps:
  - "cd {{project_name}}"
  - "python -m venv venv"
  - "source venv/bin/activate"
  - "pip install -e \".[dev]\""
  - "cp .env.example .env"
  - "# Add your Discord bot token to .env"
  - "python -m {{project_name_snake}}.bot"
```

### Step 3: Create Template Files

**README.md:**
```markdown
# {{project_name}}

{{description}}

## Installation

\`\`\`bash
pip install -e ".[dev]"
\`\`\`

## Usage

\`\`\`bash
python -m {{project_name_snake}}.bot
\`\`\`

## Author

{{author}} <{{email}}>

## License

{{license}}
```

**pyproject.toml:**
```toml
[project]
name = "{{project_name}}"
version = "0.1.0"
description = "{{description}}"
authors = [
    {name = "{{author}}", email = "{{email}}"}
]
requires-python = ">=3.10"

dependencies = [
    "discord.py>=2.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
]
```

**bot.py:**
```python
"""{{project_name}} - Discord Bot"""

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run("YOUR_TOKEN_HERE")
```

### Step 4: Test Your Template

```python
# List available templates
from athena.templates.loader import TemplateLoader

loader = TemplateLoader()
templates = loader.list_templates()
for t in templates:
    print(f"{t['type']}: {t['name']}")
```

You should see your `python-discord-bot` template listed!

Now create a project:
```
User: Create a python-discord-bot project called "my-bot" for managing my community
```

---

## Template Variables

### Available Variables

All variables use the `{{variable}}` syntax:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{project_name}}` | Project name (kebab-case) | `my-discord-bot` |
| `{{project_name_snake}}` | Project name (snake_case) | `my_discord_bot` |
| `{{description}}` | Project description | `A fun Discord bot` |
| `{{author}}` | Author name | `John Doe` |
| `{{email}}` | Author email | `john@example.com` |
| `{{license}}` | License type | `MIT`, `Apache-2.0` |
| `{{year}}` | Current year | `2026` |

### Auto-Generated Variables

- `{{project_name_snake}}`: Automatically generated from `project_name` by replacing hyphens and spaces with underscores

### Using Variables

**In file paths:**
```yaml
- path: "{{project_name_snake}}/main.py"
  template: "main.py"
```

**In template content:**
```python
"""{{project_name}} - {{description}}"""
__author__ = "{{author}}"
```

**In structure.yaml:**
```yaml
next_steps:
  - "cd {{project_name}}"
  - "python -m {{project_name_snake}}.main"
```

### Variable Substitution in Template Paths

You can use variables in template file names:

```yaml
- path: "LICENSE"
  template: "base/LICENSE.{{license}}"
```

This will load different LICENSE files based on the license choice:
- `license=MIT` → loads `base/LICENSE.MIT`
- `license=Apache-2.0` → loads `base/LICENSE.Apache-2.0`

---

## How Athena Finds Templates

### Template Discovery Process

1. **User requests a project**: "Create a python-web project"
2. **Athena extracts type**: `python-web`
3. **Searches for template** in order:
   - **User templates first**: `~/.athena/templates/python/web/structure.yaml`
   - **System templates second**: `athena/templates/python/web/structure.yaml`
4. **Loads first match** and renders project

### Priority: User Templates Override System Templates

If you create `~/.athena/templates/python/web/structure.yaml`, it will be used INSTEAD of the system template.

This allows you to:
- Customize existing templates
- Override system defaults
- Create company-specific versions

### Template Type Parsing

```
python-web → python/web
python-discord-bot → python/discord-bot
node-express-api → node/express-api
rust-actix-web → rust/actix-web
```

The first part before the hyphen is the language directory, everything after becomes the project type subdirectory.

### File Path Resolution

When loading template files, Athena searches in this order:

1. **System templates directory**: `athena/templates/{template_path}`
2. **Template-relative path**: `{template_directory}/{template_path}`

Example for custom template at `~/.athena/templates/python/discord-bot/`:

```yaml
files:
  - path: "README.md"
    template: "README.md"  # Looks in ~/.athena/templates/python/discord-bot/README.md

  - path: "LICENSE"
    template: "base/LICENSE.MIT"  # Looks in athena/templates/base/LICENSE.MIT

  - path: ".gitignore"
    template: "python/.gitignore"  # Looks in athena/templates/python/.gitignore
```

**Best Practice**:
- Custom templates should reference template files with just the filename (`README.md`)
- Reuse system templates for common files like `.gitignore` and `LICENSE` (`python/.gitignore`, `base/LICENSE.MIT`)

---

## Advanced Features

### Inline Content vs Template Files

**Template File** (recommended for large files):
```yaml
- path: "main.py"
  template: "main.py"
```

**Inline Content** (good for small files):
```yaml
- path: "{{project_name_snake}}/__init__.py"
  content: '"""{{project_name}} - {{description}}"""

__version__ = "0.1.0"
'
```

### Sharing Templates Across Projects

You can reference system templates from custom templates:

```yaml
files:
  # Use system Python gitignore
  - path: ".gitignore"
    template: "python/.gitignore"

  # Use system MIT license
  - path: "LICENSE"
    template: "base/LICENSE.MIT"

  # Use custom template file
  - path: "main.py"
    template: "main.py"
```

### Conditional Files with Variable Substitution

Use variable substitution in template paths for conditional files:

```yaml
files:
  - path: "LICENSE"
    template: "base/LICENSE.{{license}}"
```

Now Athena will load:
- `base/LICENSE.MIT` if user chooses MIT
- `base/LICENSE.Apache-2.0` if user chooses Apache-2.0

### Complex Directory Structures

```yaml
directories:
  - "src/{{project_name_snake}}"
  - "src/{{project_name_snake}}/api"
  - "src/{{project_name_snake}}/models"
  - "src/{{project_name_snake}}/utils"
  - "tests/unit"
  - "tests/integration"
  - "docs"
  - ".github/workflows"
```

### Dependencies Section

The `dependencies` section is for documentation purposes. It appears in the generated README and terminal output:

```yaml
dependencies:
  main:
    - "fastapi>=0.104.0"
    - "uvicorn[standard]>=0.24.0"
  dev:
    - "pytest>=7.4.0"
    - "black>=23.0.0"
  optional:
    - "redis>=5.0.0"  # For caching
```

---

## Best Practices

### 1. Use Clear, Descriptive Names

```yaml
name: "Python Discord Bot"  # Good
name: "Bot"  # Bad - too vague
```

### 2. Comprehensive Documentation

Always include a detailed README template with:
- Installation instructions
- Usage examples
- Configuration guide
- Development setup
- Contributing guidelines

### 3. Include Essential Files

Every template should have:
- README.md
- LICENSE
- .gitignore
- Test setup
- CI/CD configuration

### 4. Leverage System Templates

Don't recreate common files:

```yaml
files:
  - path: ".gitignore"
    template: "python/.gitignore"  # Use system template

  - path: "LICENSE"
    template: "base/LICENSE.{{license}}"  # Use system license templates
```

### 5. Provide Clear Next Steps

```yaml
next_steps:
  - "cd {{project_name}}"
  - "python -m venv venv"
  - "source venv/bin/activate"
  - "pip install -e \".[dev]\""
  - "# Configure .env file with your settings"
  - "pytest  # Run tests to verify setup"
```

### 6. Use Consistent Naming Conventions

- Template type: `language-framework` or `language-purpose`
- Files: Follow language conventions (snake_case for Python, kebab-case for Node)
- Variables: Use existing variable names when possible

### 7. Include Tests

Every template should include:
- Test directory structure
- Example test files
- Test configuration (pytest.ini, jest.config.js, etc.)
- Test runner in CI/CD

### 8. Document Dependencies

List all dependencies with minimum versions:

```yaml
dependencies:
  main:
    - "fastapi>=0.104.0"  # Specify minimum version
  dev:
    - "pytest>=7.4.0"
```

### 9. Consider Multiple Use Cases

Add configuration options for different scenarios:

```yaml
# Example: Support both SQLite and PostgreSQL
files:
  - path: "config.py"
    template: "config.py"  # Include both database configs with comments
```

### 10. Version Your Templates

Include version in structure.yaml for tracking:

```yaml
name: "Python Web API"
version: "1.0.0"
type: "python-web"
```

---

## Troubleshooting

### Template Not Found

**Symptom**: `❌ Template not found for type: python-discord-bot`

**Solutions**:
1. Check directory structure matches template type:
   ```bash
   # For python-discord-bot, need:
   ~/.athena/templates/python/discord-bot/structure.yaml
   ```

2. Verify structure.yaml exists and is valid YAML

3. Check template type matches directory name:
   ```yaml
   type: "python-discord-bot"  # Must match python/discord-bot path
   ```

### Empty Files Generated

**Symptom**: Files are created but have no content

**Solutions**:
1. Check template file paths are relative to structure.yaml directory:
   ```yaml
   files:
     - path: "README.md"
       template: "README.md"  # Good - looks in template directory
   ```

2. Verify template files actually exist:
   ```bash
   ls ~/.athena/templates/python/discord-bot/
   # Should show: README.md, structure.yaml, etc.
   ```

3. Check for typos in template filenames

### Variables Not Substituted

**Symptom**: See literal `{{project_name}}` in generated files

**Solutions**:
1. Use double curly braces: `{{variable}}` not `{variable}`

2. Check variable name spelling:
   ```
   {{project_name}}  ✓ Correct
   {{projectName}}   ✗ Wrong
   ```

3. Verify variable is supported (see Available Variables section)

### Template Not Listed

**Symptom**: `athena templates list` doesn't show your template

**Solutions**:
1. Ensure structure.yaml is valid YAML (use YAML validator)

2. Check file permissions:
   ```bash
   chmod 644 ~/.athena/templates/python/discord-bot/structure.yaml
   ```

3. Verify directory structure is correct

### License File Empty

**Symptom**: LICENSE file exists but is empty

**Solutions**:
1. Check system templates exist:
   ```bash
   ls athena/templates/base/
   # Should show: LICENSE.MIT, LICENSE.Apache-2.0, etc.
   ```

2. Verify license variable substitution:
   ```yaml
   - path: "LICENSE"
     template: "base/LICENSE.{{license}}"  # Note the variable
   ```

3. Check license parameter is passed correctly

### Import Errors in Generated Project

**Symptom**: `ModuleNotFoundError` when running generated project

**Solutions**:
1. Verify package name matches directory structure:
   ```yaml
   # If project_name = "my-bot"
   directories:
     - "{{project_name_snake}}"  # Creates my_bot/

   # In templates, import as:
   from my_bot.config import settings  # Not from my-bot
   ```

2. Check `__init__.py` files are created:
   ```yaml
   - path: "{{project_name_snake}}/__init__.py"
     content: ""  # Empty file is fine
   ```

---

## Examples

### Example 1: Python CLI Tool Template

```bash
# Create directory
mkdir -p ~/.athena/templates/python/cli

# Create structure.yaml
cat > ~/.athena/templates/python/cli/structure.yaml << 'EOF'
name: "Python CLI Tool"
type: "python-cli"
description: "Command-line tool with Click and rich output"

directories:
  - "{{project_name_snake}}"
  - "tests"

files:
  - path: "README.md"
    template: "README.md"

  - path: "{{project_name_snake}}/cli.py"
    template: "cli.py"

  - path: "{{project_name_snake}}/__init__.py"
    content: '__version__ = "0.1.0"'

dependencies:
  main:
    - "click>=8.0.0"
    - "rich>=13.0.0"
  dev:
    - "pytest>=7.4.0"

next_steps:
  - "cd {{project_name}}"
  - "pip install -e \".[dev]\""
  - "{{project_name_snake}} --help"
EOF
```

### Example 2: React TypeScript Template

```bash
mkdir -p ~/.athena/templates/javascript/react-app

cat > ~/.athena/templates/javascript/react-app/structure.yaml << 'EOF'
name: "React TypeScript App"
type: "javascript-react-app"
description: "React app with TypeScript, Vite, and Tailwind CSS"

directories:
  - "src"
  - "src/components"
  - "src/hooks"
  - "src/utils"
  - "public"

files:
  - path: "package.json"
    template: "package.json"

  - path: "tsconfig.json"
    template: "tsconfig.json"

  - path: "src/App.tsx"
    template: "App.tsx"

dependencies:
  main:
    - "react@^18.2.0"
    - "react-dom@^18.2.0"
  dev:
    - "typescript@^5.0.0"
    - "vite@^5.0.0"
    - "@vitejs/plugin-react@^4.0.0"

next_steps:
  - "cd {{project_name}}"
  - "npm install"
  - "npm run dev"
EOF
```

---

## Sharing Templates

### With Your Team

1. Create templates in a shared repository
2. Team members clone to `~/.athena/templates/`
3. Everyone uses same company standards

```bash
# Clone company templates
git clone https://github.com/yourcompany/athena-templates ~/.athena/templates
```

### With the Community

1. Create a GitHub repository with your templates
2. Share on Athena discussions/issues
3. Users can install with:

```bash
git clone https://github.com/username/awesome-athena-templates ~/.athena/templates
```

---

## Next Steps

1. **Create your first template** following the Quick Start guide
2. **Test it** by creating a project with Athena
3. **Refine** based on what you learn
4. **Share** with your team or the community!

For more examples, see the system templates in `athena/templates/`.

---

**Need Help?**
- Check [TEMPLATE_ROADMAP.md](TEMPLATE_ROADMAP.md) for inspiration
- See system templates in `athena/templates/` for reference
- Open an issue on GitHub for support

**Happy templating!** 🚀
