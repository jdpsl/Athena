"""CLI interface for Athena."""

import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from athena.models.config import AthenaConfig
from athena.agent.main_agent import MainAgent
from athena.tools.base import ToolRegistry
from athena.tools.file_ops import ReadTool, WriteTool, EditTool, InsertTool
from athena.tools.search import GlobTool, GrepTool
from athena.tools.bash import BashTool
from athena.tools.todo import TodoWriteTool
from athena.queue.sqlite_queue import SQLiteJobQueue
from athena.hooks.manager import HookManager
from athena.commands.loader import CommandLoader
from athena.config_manager import PersistentConfigManager
from athena.mcp.manager import MCPClientManager


console = Console()


class AthenaSession:
    """Athena interactive session."""

    def __init__(self, config: AthenaConfig):
        """Initialize session.

        Args:
            config: Athena configuration
        """
        self.config = config
        self.job_queue: SQLiteJobQueue | None = None
        self.agent: MainAgent | None = None
        self.tool_registry = ToolRegistry()
        self.hook_manager = HookManager()
        self.command_loader = CommandLoader()
        self.config_manager = PersistentConfigManager()
        self.mcp_manager: MCPClientManager | None = None
        self.skill_loader = None

    async def initialize(self) -> None:
        """Initialize the session."""
        # Initialize job queue
        self.job_queue = SQLiteJobQueue()
        await self.job_queue.initialize()

        # Register basic tools first
        self._register_tools()

        # Register Task tool (needs job queue)
        from athena.tools.task import TaskTool
        task_tool = TaskTool(
            config=self.config,
            tool_registry=self.tool_registry,
            job_queue=self.job_queue,
        )
        self.tool_registry.register(task_tool)

        # Initialize MCP clients and register MCP tools
        if self.config.mcp.enabled:
            self.mcp_manager = MCPClientManager(self.config.mcp)
            await self.mcp_manager.initialize_all(self.tool_registry)

        # Initialize skills
        from athena.skills.loader import SkillLoader
        self.skill_loader = SkillLoader(working_directory=self.config.working_directory)
        self.skill_loader.discover_skills()

        # Initialize agent
        self.agent = MainAgent(self.config, self.tool_registry, self.job_queue)

        # Pass LLM client to WebFetch for AI-enhanced extraction
        if hasattr(self, '_web_fetch_tool'):
            self._web_fetch_tool.llm_client = self.agent.llm_client

        # Load slash commands
        self.command_loader.load_commands()

        # Add system prompt
        self.agent.add_system_message(self._get_system_prompt())

    def _register_tools(self) -> None:
        """Register all available tools."""
        from athena.tools.web import WebSearchTool, WebFetchTool
        from athena.tools.user_interaction import AskUserQuestionTool
        from athena.tools.git import GitStatusTool, GitDiffTool, GitCommitTool, GitLogTool, GitBranchTool
        from athena.tools.file_system import DeleteFileTool, MoveFileTool, CopyFileTool, ListDirTool, MakeDirTool

        # File operations
        self.tool_registry.register(ReadTool())
        self.tool_registry.register(WriteTool())
        self.tool_registry.register(EditTool())
        self.tool_registry.register(InsertTool())
        self.tool_registry.register(DeleteFileTool())
        self.tool_registry.register(MoveFileTool())
        self.tool_registry.register(CopyFileTool())
        self.tool_registry.register(ListDirTool())
        self.tool_registry.register(MakeDirTool())

        # Search tools
        self.tool_registry.register(GlobTool())
        self.tool_registry.register(GrepTool())

        # Execution
        self.tool_registry.register(BashTool(timeout_ms=self.config.tools.bash_timeout))

        # Task management
        self.tool_registry.register(TodoWriteTool())

        # Git tools
        self.tool_registry.register(GitStatusTool())
        self.tool_registry.register(GitDiffTool())
        self.tool_registry.register(GitCommitTool())
        self.tool_registry.register(GitLogTool())
        self.tool_registry.register(GitBranchTool())

        # Web tools
        self.tool_registry.register(WebSearchTool())
        self._web_fetch_tool = WebFetchTool()  # Gets LLM client after agent is created
        self.tool_registry.register(self._web_fetch_tool)

        # User interaction
        self.tool_registry.register(AskUserQuestionTool())

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent.

        Returns:
            System prompt
        """
        return """You are Athena, an AI coding assistant. You help users with software engineering tasks.

You have access to tools for:
- File operations: Read, Write, Edit, Insert, Delete, Move, Copy, ListDir, MakeDir
- Search: Glob (find files by pattern), Grep (search file contents with regex)
- Execution: Bash (run shell commands - tests, builds, package management, git add, etc.)
- Git: GitStatus, GitDiff, GitCommit, GitLog, GitBranch
- Task management: TodoWrite for tracking multi-step tasks
- Agent spawning: Task tool to spawn specialized sub-agents for complex work
- Web access: WebSearch (internet search), WebFetch (fetch web pages)
- User interaction: AskUserQuestion (ask clarifying questions)

File Operations:
- Read - View file contents (ALWAYS use before Edit, Insert, or Write!)
- Edit - Make precise changes to existing files (requires Read first)
- Insert - Insert text at a specific line number (requires Read first)
  * Use insert_line=0 to insert at the beginning of the file
  * Use insert_line=N to insert after line N (1-indexed)
  * Perfect for adding imports, docstrings, or new functions without replacing text
- Write - Create new files or completely overwrite existing ones
- DeleteFile - Remove files/directories (use with caution!)
- MoveFile - Move or rename files
- CopyFile - Duplicate files/directories
- ListDir - List directory contents with details (better than 'ls')
- MakeDir - Create directories
IMPORTANT: You MUST Read a file before using Edit, Insert, or Write on it!

Search Tools - Use for finding files and content:
- Glob - Find files by pattern:
  Examples: "**/*.py" (all Python files), "src/**/*.ts" (TypeScript in src)
  Use when: Finding files by name, extension, or path pattern
- Grep - Search file contents with regex:
  Examples: pattern="def main", pattern="class.*User", pattern="TODO:"
  Use when: Finding where code/text exists, searching for functions/classes
  Can use with -i for case-insensitive, output_mode for different views

Bash Tool - Use for shell operations:
- Running tests: pytest, npm test, cargo test
- Installing dependencies: pip install, npm install, cargo build
- Building projects: npm run build, make, go build
- Git staging: git add <files> (required before GitCommit)
- Package management: pip, npm, cargo, apt
- System commands: ls, find, grep (when specialized tools won't work)
- File manipulation that needs shell features
IMPORTANT: Proactively use Bash for these tasks - don't ask the user first!

Git Tools (use these for viewing/committing, but use Bash for 'git add'):
- GitStatus - See current changes, staged files, branch info
- GitDiff - View diffs (staged or unstaged)
- GitCommit - Create commits (use Bash to 'git add' files first!)
- GitLog - View commit history
- GitBranch - List, create, switch, or delete branches

User Interaction:
- AskUserQuestion - When you need clarification, ask the user!
  Examples: "Which approach?", "What should X be?", "Is this correct?"

Task Management:
- TodoWrite - Track progress on multi-step tasks:
  Use when: Task has 3+ steps, user gives multiple requests, complex planning needed
  Creates visible todo list so user can see your progress
  IMPORTANT: Use proactively! Update status as you work (pending → in_progress → completed)
  Examples: "Add dark mode" (multiple files), "Fix 5 bugs" (multiple items)

The Task tool lets you spawn specialized agents for complex work:
- Explore: Navigate and understand codebases
  Use when: User asks "where is X?", "how does Y work?", "find all Z"
  Example: "Where is authentication handled?" → spawn Explore agent
- Plan: Break down tasks into implementation steps
  Use when: Large features, architectural changes, unclear scope
  Example: "Add real-time updates" → spawn Plan agent to design approach
- code-reviewer: Review code quality and security
  Use when: After writing significant code, user asks for review
- test-runner: Run and analyze tests
  Use when: Need to run tests and debug failures
- general-purpose: Handle complex multi-step tasks
  Use when: Task requires multiple tools and careful coordination

Web Tools:
- WebSearch: Search the internet for information, documentation, examples
- WebFetch: Fetch and read content from URLs (converts HTML to clean text)
  - Simple mode: Just fetches and cleans the content
  - AI mode: Use extract_prompt parameter to extract specific information
- IMPORTANT: When using WebSearch, always include a "Sources:" section in your response with links

When working on tasks:
1. ALWAYS Read files before editing them (required for Edit/Write tools)
2. Use TodoWrite proactively for tasks with 3+ steps (helps user see progress)
3. Proactively use Bash for: tests, builds, installs, git add, shell operations
4. Use Search tools (Glob/Grep) to find files and code before making assumptions
5. Use AskUserQuestion if you're unsure about approach or details
6. Use specialized Git tools (GitStatus, GitDiff, etc.) for viewing git state
7. Use Task tool to spawn sub-agents for complex exploration or planning
8. Use WebSearch and WebFetch when you need docs or encounter unfamiliar tech
9. Use file operation tools (Read, Write, Edit, Insert) instead of cat/echo for file ops
10. Always test your changes by running tests with Bash
11. Be thorough and careful with code changes

You are running in a persistent session. The user is working on a coding project."""

    async def run_interactive(self) -> None:
        """Run interactive REPL."""
        console.print(
            Panel.fit(
                "[bold cyan]Athena AI[/bold cyan]\n"
                "Open-source AI agent for coding assistance\n"
                "Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit",
                border_style="cyan",
            )
        )

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if not user_input.strip():
                    continue

                # Handle built-in commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        continue

                # Expand slash commands
                expanded_input = self.command_loader.expand_command(user_input)

                # Check if this is a documentation question
                if self._is_documentation_question(expanded_input):
                    # Spawn docs agent
                    console.print("\n[bold cyan]Athena[/bold cyan]")
                    response = await self._spawn_docs_agent(expanded_input)
                    console.print(Markdown(response))
                else:
                    # Run main agent
                    console.print("\n[bold cyan]Athena[/bold cyan]")
                    response = await self.agent.run(expanded_input)
                    console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                if self.config.debug:
                    import traceback

                    traceback.print_exc()

    async def _handle_command(self, command: str) -> bool:
        """Handle built-in commands.

        Args:
            command: Command string

        Returns:
            True if command was handled, False to continue processing
        """
        cmd = command.lower().split()[0]

        if cmd in ["/exit", "/quit"]:
            console.print("[cyan]Goodbye![/cyan]")
            if self.job_queue:
                await self.job_queue.close()
            exit(0)

        elif cmd == "/help":
            console.print(
                Panel(
                    """[bold]Built-in Commands:[/bold]
/help - Show this help
/exit - Exit Athena
/clear - Clear conversation history
/config - Show current configuration
/model [name] - Show or set model
/api [url] - Show or set API base URL
/apikey [key] - Show or set API key
/temp [value] - Show or set temperature (0.0-1.0)
/fallback [on|off] - Toggle text-based tool calling fallback
/thinking [on|off] - Toggle thinking tag injection (extended reasoning)
/save - Save current settings to ~/.athena/config.json
/tools - List available tools
/commands - List slash commands
/skills - List available skills
/skill <name> [task] - Invoke a skill
/mcp-list - List all MCP servers
/mcp-add <name> <transport> <command/url> [args...] - Add MCP server
/mcp-remove <name> - Remove MCP server
/mcp-enable <name> - Enable MCP server
/mcp-disable <name> - Disable MCP server

[bold]Examples:[/bold]
/model gpt-4
/api https://api.openai.com/v1
/apikey sk-1234567890abcdef
/temp 0.5
/fallback on
/save

[bold]Fallback Mode:[/bold]
Enable for models without native function calling support
Uses text format: TOOL[Name]{"param": "value"}

[bold]Persistent Settings:[/bold]
Settings saved with /save are automatically loaded on startup
Config location: ~/.athena/config.json

[bold]Custom Commands:[/bold]
Create .athena/commands/*.md files to define custom slash commands
""",
                    title="Athena Help",
                    border_style="cyan",
                )
            )
            return True

        elif cmd == "/clear":
            self.agent.clear_history()
            self.agent.add_system_message(self._get_system_prompt())
            console.print("[green]Conversation history cleared[/green]")
            return True

        elif cmd == "/config":
            console.print(
                Panel(
                    f"[cyan]Model:[/cyan] {self.config.llm.model}\n"
                    f"[cyan]API Base:[/cyan] {self.config.llm.api_base}\n"
                    f"[cyan]Temperature:[/cyan] {self.config.llm.temperature}\n"
                    f"[cyan]Max Iterations:[/cyan] {self.config.agent.max_iterations}\n"
                    f"[cyan]Thinking Enabled:[/cyan] {self.config.agent.enable_thinking}\n"
                    f"[cyan]Fallback Mode:[/cyan] {self.config.agent.fallback_mode}",
                    title="Current Configuration",
                    border_style="cyan",
                )
            )
            return True

        elif cmd == "/model":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set model
                new_model = parts[1]
                self.config.llm.model = new_model
                # Update the LLM client with new model
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] Model set to: [cyan]{new_model}[/cyan]")
            else:
                # Show current model
                console.print(f"[cyan]Current model:[/cyan] {self.config.llm.model}")
            return True

        elif cmd == "/api":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set API base
                new_api = parts[1]
                self.config.llm.api_base = new_api
                # Update the LLM client
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] API base set to: [cyan]{new_api}[/cyan]")
            else:
                # Show current API base
                console.print(f"[cyan]Current API base:[/cyan] {self.config.llm.api_base}")
            return True

        elif cmd == "/temp":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set temperature
                try:
                    new_temp = float(parts[1])
                    if 0.0 <= new_temp <= 1.0:
                        self.config.llm.temperature = new_temp
                        console.print(f"[green]✓[/green] Temperature set to: [cyan]{new_temp}[/cyan]")
                    else:
                        console.print("[red]Error:[/red] Temperature must be between 0.0 and 1.0")
                except ValueError:
                    console.print("[red]Error:[/red] Temperature must be a number")
            else:
                # Show current temperature
                console.print(f"[cyan]Current temperature:[/cyan] {self.config.llm.temperature}")
            return True

        elif cmd == "/apikey":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set API key
                new_key = parts[1]
                self.config.llm.api_key = new_key
                # Update the LLM client
                from athena.llm.thinking_injector import ThinkingInjector
                from athena.llm.client import LLMClient
                thinking_injector = ThinkingInjector(
                    enable_thinking=self.config.agent.enable_thinking,
                    thinking_budget=self.config.agent.thinking_budget,
                )
                self.agent.llm_client = LLMClient(self.config.llm, thinking_injector)
                console.print(f"[green]✓[/green] API key set")
            else:
                # Show current API key (masked)
                if self.config.llm.api_key:
                    masked = self.config.llm.api_key[:8] + "..." if len(self.config.llm.api_key) > 8 else "***"
                    console.print(f"[cyan]Current API key:[/cyan] {masked}")
                else:
                    console.print("[yellow]No API key set[/yellow]")
            return True

        elif cmd == "/save":
            # Save current settings to ~/.athena/config.json
            # Convert MCP servers to dict for JSON serialization
            mcp_servers = [
                {
                    "name": s.name,
                    "transport": s.transport,
                    "command": s.command,
                    "args": s.args,
                    "env": s.env,
                    "url": s.url,
                    "enabled": s.enabled,
                    "timeout": s.timeout,
                }
                for s in self.config.mcp.servers
            ] if self.config.mcp.servers else None

            settings = self.config_manager.get_current_settings(
                model=self.config.llm.model,
                api_base=self.config.llm.api_base,
                api_key=self.config.llm.api_key,
                temperature=self.config.llm.temperature,
                mcp_servers=mcp_servers,
            )
            if self.config_manager.save(settings):
                console.print("[green]✓[/green] Settings saved to ~/.athena/config.json")
                console.print(f"  [cyan]Model:[/cyan] {settings['model']}")
                console.print(f"  [cyan]API Base:[/cyan] {settings['api_base']}")
                console.print(f"  [cyan]API Key:[/cyan] {'Set' if settings['api_key'] else 'Not set'}")
                console.print(f"  [cyan]Temperature:[/cyan] {settings['temperature']}")
                if mcp_servers:
                    console.print(f"  [cyan]MCP Servers:[/cyan] {len(mcp_servers)} saved")
            else:
                console.print("[red]Error:[/red] Failed to save settings")
            return True

        elif cmd == "/fallback":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set fallback mode
                value = parts[1].lower()
                if value in ['on', 'true', '1', 'yes']:
                    self.config.agent.fallback_mode = True
                    # Reinitialize agent with fallback parser
                    from athena.llm.fallback_parser import FallbackToolParser
                    self.agent.fallback_parser = FallbackToolParser()
                    # Re-inject system prompt with fallback instructions
                    if self.agent.messages and self.agent.messages[0].role.value == 'system':
                        original_prompt = self.agent.messages[0].content.split('\n\n## IMPORTANT: Tool Calling Format')[0]
                        self.agent.messages[0].content = self.agent.fallback_parser.inject_instructions(original_prompt)
                    console.print("[green]✓[/green] Fallback mode [bold]enabled[/bold]")
                    console.print("  [dim]Using text-based tool calling (TOOL[Name]{args})[/dim]")
                elif value in ['off', 'false', '0', 'no']:
                    self.config.agent.fallback_mode = False
                    self.agent.fallback_parser = None
                    # Restore system prompt without fallback instructions
                    if self.agent.messages and self.agent.messages[0].role.value == 'system':
                        self.agent.messages[0].content = self.agent.messages[0].content.split('\n\n## IMPORTANT: Tool Calling Format')[0]
                    console.print("[green]✓[/green] Fallback mode [bold]disabled[/bold]")
                    console.print("  [dim]Using native function calling[/dim]")
                else:
                    console.print("[red]Error:[/red] Use 'on' or 'off'")
            else:
                # Show current state
                status = "[green]enabled[/green]" if self.config.agent.fallback_mode else "[red]disabled[/red]"
                console.print(f"[cyan]Fallback mode:[/cyan] {status}")
                console.print("\n[dim]Fallback mode uses text-based tool calling for models")
                console.print("without native function calling support.[/dim]")
            return True

        elif cmd == "/thinking":
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                # Set thinking mode
                value = parts[1].lower()
                if value in ['on', 'true', '1', 'yes']:
                    self.config.agent.enable_thinking = True
                    console.print("[green]✓[/green] Thinking tag injection [bold]enabled[/bold]")
                    console.print("  [dim]Extended reasoning will be injected for supported models[/dim]")
                elif value in ['off', 'false', '0', 'no']:
                    self.config.agent.enable_thinking = False
                    console.print("[green]✓[/green] Thinking tag injection [bold]disabled[/bold]")
                    console.print("  [dim]Model will use standard reasoning without thinking tags[/dim]")
                else:
                    console.print("[red]Error:[/red] Use 'on' or 'off'")
            else:
                # Show current state
                status = "[green]enabled[/green]" if self.config.agent.enable_thinking else "[red]disabled[/red]"
                console.print(f"[cyan]Thinking tag injection:[/cyan] {status}")
                console.print(f"[cyan]Thinking budget:[/cyan] {self.config.agent.thinking_budget} tokens")
                console.print("\n[dim]Thinking tag injection enables extended reasoning for models that support <thinking> tags (improves complex problem solving).[/dim]")
            return True

        elif cmd == "/tools":
            tools = self.tool_registry.list_tools()
            console.print("[bold cyan]Available Tools:[/bold cyan]")
            for tool in tools:
                console.print(f"  • [green]{tool.name}[/green]: {tool.description}")
            return True

        elif cmd == "/commands":
            commands = self.command_loader.list_commands()
            if commands:
                console.print("[bold cyan]Available Commands:[/bold cyan]")
                for cmd_name in commands:
                    console.print(f"  • /{cmd_name}")
            else:
                console.print("[yellow]No custom commands found[/yellow]")
            return True

        elif cmd == "/skills":
            await self._handle_skills_list()
            return True

        elif cmd == "/skill":
            await self._handle_skill_invoke(command)
            return True

        elif cmd == "/mcp-list":
            await self._handle_mcp_list()
            return True

        elif cmd == "/mcp-add":
            await self._handle_mcp_add(command)
            return True

        elif cmd == "/mcp-remove":
            await self._handle_mcp_remove(command)
            return True

        elif cmd == "/mcp-enable":
            await self._handle_mcp_enable(command)
            return True

        elif cmd == "/mcp-disable":
            await self._handle_mcp_disable(command)
            return True

        return False

    def _is_documentation_question(self, text: str) -> bool:
        """Detect if user input is a documentation question.

        Args:
            text: User input text

        Returns:
            True if this appears to be a documentation question
        """
        text_lower = text.lower()

        # Documentation question patterns
        doc_patterns = [
            # Questions about capabilities
            "can athena",
            "does athena",
            "is athena",
            "what can athena",
            "what does athena",
            # Questions about how-to
            "how do i",
            "how can i",
            "how to",
            "how does",
            # Questions about configuration
            "how do i configure",
            "how do i set up",
            "how do i enable",
            "how do i use",
            # Questions about features
            "what tools",
            "what commands",
            "what features",
            "what is",
            "what are",
            # Questions about MCP
            "what is mcp",
            "how does mcp",
            "mcp server",
            # General help
            "help me with",
            "tell me about",
            "explain",
        ]

        return any(pattern in text_lower for pattern in doc_patterns)

    async def _spawn_docs_agent(self, question: str) -> str:
        """Spawn athena-docs agent to answer documentation question.

        Args:
            question: Documentation question from user

        Returns:
            Answer from docs agent
        """
        from athena.agent.types import AgentType, get_system_prompt
        from athena.agent.executor import AgentExecutor
        from athena.llm.client import LLMClient
        from athena.models.message import Message, Role

        # Create a dedicated LLM client for the docs agent
        docs_client = LLMClient(self.config.llm)

        # Create limited tool registry with only search/read tools
        from athena.tools.base import ToolRegistry
        docs_tools = ToolRegistry()
        docs_tools.register(GlobTool())
        docs_tools.register(GrepTool())
        docs_tools.register(ReadTool())

        # Create docs agent executor
        docs_agent = AgentExecutor(
            llm_client=docs_client,
            tool_registry=docs_tools,
            config=self.config.agent,
        )

        # Get system prompt for docs agent
        system_prompt = get_system_prompt(AgentType.ATHENA_DOCS)

        # Build messages
        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=question),
        ]

        # Run the agent
        console.print("[dim]🔍 Looking up documentation...[/dim]")
        result = await docs_agent.run(messages)

        return result.content

    async def _handle_mcp_list(self) -> None:
        """Handle /mcp-list command."""
        if not self.config.mcp.servers:
            console.print("[yellow]No MCP servers configured[/yellow]")
            console.print("\n[dim]Add a server with: /mcp-add <name> <transport> <command/url> [args...][/dim]")
            return

        console.print("[bold cyan]MCP Servers:[/bold cyan]\n")
        for server in self.config.mcp.servers:
            status = "[green]●[/green]" if server.enabled else "[red]○[/red]"
            connected = "✓" if self.mcp_manager and server.name in self.mcp_manager.clients else "✗"

            console.print(f"{status} [bold]{server.name}[/bold] ({server.transport}) [{connected}]")
            if server.transport == "stdio":
                console.print(f"   Command: {server.command} {' '.join(server.args)}")
                if server.env:
                    console.print(f"   Env: {', '.join(f'{k}={v}' for k, v in server.env.items())}")
            else:  # http
                console.print(f"   URL: {server.url}")

            # Show tools from this server
            if self.mcp_manager and server.name in self.mcp_manager.clients:
                mcp_tools = [name for name in self.tool_registry.tools.keys() if name.startswith(f"{server.name}:")]
                if mcp_tools:
                    console.print(f"   Tools: {', '.join(mcp_tools)}")
            console.print()

    async def _handle_mcp_add(self, command: str) -> None:
        """Handle /mcp-add command."""
        parts = command.split()
        if len(parts) < 4:
            console.print("[red]Error:[/red] Usage: /mcp-add <name> <transport> <command/url> [args...]")
            console.print("\n[bold]Examples:[/bold]")
            console.print("  /mcp-add test stdio python3 test_mcp_server.py")
            console.print("  /mcp-add postgres stdio python -m mcp_server_postgres")
            console.print("  /mcp-add api http http://localhost:8000/mcp")
            return

        name = parts[1]
        transport = parts[2].lower()

        if transport not in ["stdio", "http"]:
            console.print("[red]Error:[/red] Transport must be 'stdio' or 'http'")
            return

        # Check if server already exists
        if any(s.name == name for s in self.config.mcp.servers):
            console.print(f"[red]Error:[/red] MCP server '{name}' already exists")
            console.print(f"[dim]Use /mcp-remove {name} first to replace it[/dim]")
            return

        from athena.models.config import MCPServerConfig

        if transport == "stdio":
            command_str = parts[3]
            args = parts[4:] if len(parts) > 4 else []
            server_config = MCPServerConfig(
                name=name,
                transport="stdio",
                command=command_str,
                args=args,
                enabled=True
            )
        else:  # http
            url = parts[3]
            server_config = MCPServerConfig(
                name=name,
                transport="http",
                url=url,
                enabled=True
            )

        # Add to config
        self.config.mcp.servers.append(server_config)
        console.print(f"[green]✓[/green] Added MCP server: [cyan]{name}[/cyan]")

        # Connect to the new server
        if not self.config.mcp.enabled:
            self.config.mcp.enabled = True
            console.print("[yellow]Note:[/yellow] MCP was disabled, now enabled")

        if not self.mcp_manager:
            self.mcp_manager = MCPClientManager(self.config.mcp)

        console.print(f"[dim]Connecting to {name}...[/dim]")
        try:
            await self.mcp_manager._initialize_server(server_config, self.tool_registry)
            console.print(f"[green]✓[/green] Connected successfully!")

            # Show tools
            mcp_tools = [n for n in self.tool_registry.tools.keys() if n.startswith(f"{name}:")]
            if mcp_tools:
                console.print(f"   Tools available: {', '.join(mcp_tools)}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect: {e}")
            console.print("[yellow]Server added to config but not connected[/yellow]")

        console.print("\n[dim]Save with /save to persist this change[/dim]")

    async def _handle_mcp_remove(self, command: str) -> None:
        """Handle /mcp-remove command."""
        parts = command.split()
        if len(parts) != 2:
            console.print("[red]Error:[/red] Usage: /mcp-remove <name>")
            return

        name = parts[1]
        server = next((s for s in self.config.mcp.servers if s.name == name), None)

        if not server:
            console.print(f"[red]Error:[/red] MCP server '{name}' not found")
            console.print("\n[dim]Use /mcp-list to see available servers[/dim]")
            return

        # Disconnect if connected
        if self.mcp_manager and name in self.mcp_manager.clients:
            console.print(f"[dim]Disconnecting from {name}...[/dim]")
            try:
                await self.mcp_manager.clients[name].disconnect()
                del self.mcp_manager.clients[name]
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Error disconnecting: {e}")

            # Unregister tools
            tools_to_remove = [n for n in self.tool_registry.tools.keys() if n.startswith(f"{name}:")]
            for tool_name in tools_to_remove:
                self.tool_registry.tools.pop(tool_name, None)
            console.print(f"[dim]Removed {len(tools_to_remove)} tools[/dim]")

        # Remove from config
        self.config.mcp.servers = [s for s in self.config.mcp.servers if s.name != name]
        console.print(f"[green]✓[/green] Removed MCP server: [cyan]{name}[/cyan]")
        console.print("\n[dim]Save with /save to persist this change[/dim]")

    async def _handle_mcp_enable(self, command: str) -> None:
        """Handle /mcp-enable command."""
        parts = command.split()
        if len(parts) != 2:
            console.print("[red]Error:[/red] Usage: /mcp-enable <name>")
            return

        name = parts[1]
        server = next((s for s in self.config.mcp.servers if s.name == name), None)

        if not server:
            console.print(f"[red]Error:[/red] MCP server '{name}' not found")
            return

        if server.enabled:
            console.print(f"[yellow]Note:[/yellow] MCP server '{name}' is already enabled")
            return

        server.enabled = True
        console.print(f"[green]✓[/green] Enabled MCP server: [cyan]{name}[/cyan]")

        # Connect to the server
        if not self.mcp_manager:
            self.mcp_manager = MCPClientManager(self.config.mcp)

        console.print(f"[dim]Connecting to {name}...[/dim]")
        try:
            await self.mcp_manager._initialize_server(server, self.tool_registry)
            console.print(f"[green]✓[/green] Connected successfully!")

            # Show tools
            mcp_tools = [n for n in self.tool_registry.tools.keys() if n.startswith(f"{name}:")]
            if mcp_tools:
                console.print(f"   Tools available: {', '.join(mcp_tools)}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect: {e}")

        console.print("\n[dim]Save with /save to persist this change[/dim]")

    async def _handle_mcp_disable(self, command: str) -> None:
        """Handle /mcp-disable command."""
        parts = command.split()
        if len(parts) != 2:
            console.print("[red]Error:[/red] Usage: /mcp-disable <name>")
            return

        name = parts[1]
        server = next((s for s in self.config.mcp.servers if s.name == name), None)

        if not server:
            console.print(f"[red]Error:[/red] MCP server '{name}' not found")
            return

        if not server.enabled:
            console.print(f"[yellow]Note:[/yellow] MCP server '{name}' is already disabled")
            return

        # Disconnect if connected
        if self.mcp_manager and name in self.mcp_manager.clients:
            console.print(f"[dim]Disconnecting from {name}...[/dim]")
            try:
                await self.mcp_manager.clients[name].disconnect()
                del self.mcp_manager.clients[name]
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Error disconnecting: {e}")

            # Unregister tools
            tools_to_remove = [n for n in self.tool_registry.tools.keys() if n.startswith(f"{name}:")]
            for tool_name in tools_to_remove:
                self.tool_registry.tools.pop(tool_name, None)
            console.print(f"[dim]Removed {len(tools_to_remove)} tools from registry[/dim]")

        server.enabled = False
        console.print(f"[green]✓[/green] Disabled MCP server: [cyan]{name}[/cyan]")
        console.print("\n[dim]Save with /save to persist this change[/dim]")

    async def _handle_skills_list(self) -> None:
        """Handle /skills command - list all available skills."""
        if not self.skill_loader:
            console.print("[yellow]Skills system not initialized[/yellow]")
            return

        skills = self.skill_loader.list_skills()

        if not skills:
            console.print("[yellow]No skills found[/yellow]")
            console.print("\n[dim]Create skills in:[/dim]")
            console.print(f"[dim]  Global: ~/.athena/skills/[/dim]")
            console.print(f"[dim]  Project: ./.athena/skills/[/dim]")
            console.print("\n[dim]Each skill should be a directory with a SKILL.md file[/dim]")
            return

        console.print(f"[bold cyan]Available Skills ({len(skills)}):[/bold cyan]\n")

        for skill in skills:
            # Determine scope (global or project)
            if skill.skill_path.is_relative_to(Path.home() / ".athena"):
                scope = "[dim](global)[/dim]"
            else:
                scope = "[dim](project)[/dim]"

            console.print(f"  [green]{skill.name}[/green] {scope}")
            console.print(f"    {skill.description}")

            if skill.allowed_tools:
                tools_str = ", ".join(skill.allowed_tools[:5])
                if len(skill.allowed_tools) > 5:
                    tools_str += f", +{len(skill.allowed_tools) - 5} more"
                console.print(f"    [dim]Tools: {tools_str}[/dim]")

            if skill.model:
                console.print(f"    [dim]Model: {skill.model}[/dim]")

            console.print()

        console.print("[dim]Use /skill <name> to invoke a skill[/dim]")

    async def _handle_skill_invoke(self, command: str) -> None:
        """Handle /skill <name> command - invoke a skill."""
        parts = command.split(maxsplit=1)

        if len(parts) < 2:
            console.print("[red]Error:[/red] Usage: /skill <name>")
            console.print("[dim]Use /skills to list available skills[/dim]")
            return

        skill_name = parts[1].split()[0]  # Get just the skill name
        task_description = parts[1][len(skill_name):].strip() if len(parts[1]) > len(skill_name) else ""

        if not self.skill_loader:
            console.print("[yellow]Skills system not initialized[/yellow]")
            return

        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            console.print(f"[red]Error:[/red] Skill '{skill_name}' not found")
            console.print("\n[dim]Available skills:[/dim]")
            for s in self.skill_loader.list_skills():
                console.print(f"  • {s.name}")
            return

        # Ask user for task if not provided
        if not task_description:
            task_description = Prompt.ask(
                f"\n[bold green]Task for {skill.name}[/bold green]",
                default="Execute the skill"
            )

        # Show what we're doing
        console.print(f"\n[bold cyan]🎯 Activating skill:[/bold cyan] {skill.name}")
        console.print(f"[dim]{skill.description}[/dim]")
        console.print(f"\n[bold]Task:[/bold] {task_description}\n")

        # Create a skill agent with the skill's system prompt
        from athena.agent.executor import AgentExecutor
        from athena.llm.client import LLMClient
        from athena.models.message import Message, Role

        # Create LLM client (use skill's model if specified)
        llm_config = self.config.llm
        if skill.model:
            # Override model for this skill
            from athena.models.config import LLMConfig
            llm_config = LLMConfig(
                api_base=self.config.llm.api_base,
                api_key=self.config.llm.api_key,
                model=skill.model,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                timeout=self.config.llm.timeout,
            )

        skill_client = LLMClient(llm_config)

        # Create limited tool registry if allowed_tools specified
        if skill.allowed_tools:
            from athena.tools.base import ToolRegistry
            skill_tools = ToolRegistry()
            for tool_name in skill.allowed_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    skill_tools.register(tool)
                else:
                    console.print(f"[yellow]Warning:[/yellow] Tool '{tool_name}' not found")
        else:
            # Use all tools
            skill_tools = self.tool_registry

        # Create skill agent
        skill_agent = AgentExecutor(
            llm_client=skill_client,
            tool_registry=skill_tools,
            config=self.config.agent,
        )

        # Build messages with skill's system prompt
        messages = [
            Message(role=Role.SYSTEM, content=skill.get_system_prompt()),
            Message(role=Role.USER, content=task_description),
        ]

        # Run the skill agent
        try:
            result = await skill_agent.run(messages)
            console.print("\n[bold cyan]Skill Result:[/bold cyan]")
            console.print(Markdown(result.content))
        except Exception as e:
            console.print(f"\n[red]Error executing skill:[/red] {e}")
            if self.config.debug:
                import traceback
                traceback.print_exc()

    async def run_single_task(self, prompt: str) -> str:
        """Run a single task and return the result.

        Args:
            prompt: User prompt

        Returns:
            Agent response
        """
        response = await self.agent.run(prompt)
        if self.job_queue:
            await self.job_queue.close()
        return response

    async def cleanup(self) -> None:
        """Clean up resources."""
        # Disconnect MCP clients
        if self.mcp_manager:
            await self.mcp_manager.cleanup_all()

        # Close job queue
        if self.job_queue:
            await self.job_queue.close()


@click.command()
@click.option("-p", "--prompt", help="Single prompt to execute")
@click.option("--config", help="Path to config file")
@click.option("--model", help="Model name to use")
@click.option("--api-base", help="API base URL")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def main(prompt: str | None, config: str | None, model: str | None, api_base: str | None, debug: bool):
    """Athena - Open source AI agent for coding assistance."""

    # Load configuration
    if config and Path(config).exists():
        # Use specified config file
        athena_config = AthenaConfig.from_yaml(config)
    elif Path("config.yaml").exists():
        # Auto-detect config.yaml in current directory
        athena_config = AthenaConfig.from_yaml("config.yaml")
    else:
        # Fall back to environment variables
        athena_config = AthenaConfig.from_env()

    # Load saved settings from ~/.athena/config.json
    config_manager = PersistentConfigManager()
    saved_settings = config_manager.load()
    if saved_settings:
        console.print("[dim]Loading saved settings from ~/.athena/config.json[/dim]")
        config_manager.apply_to_config(athena_config, saved_settings)

    # Override with CLI args (these take precedence over saved settings)
    if model:
        athena_config.llm.model = model
    if api_base:
        athena_config.llm.api_base = api_base
    if debug:
        athena_config.debug = True

    # Run session
    async def run():
        session = AthenaSession(athena_config)
        await session.initialize()

        try:
            if prompt:
                # Single task mode
                response = await session.run_single_task(prompt)
                console.print(Markdown(response))
            else:
                # Interactive mode
                await session.run_interactive()
        finally:
            await session.cleanup()

    asyncio.run(run())


if __name__ == "__main__":
    main()
